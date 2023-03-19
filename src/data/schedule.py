from __future__ import annotations

import asyncio
import json
import logging
import traceback
from collections import defaultdict, namedtuple
from dataclasses import dataclass

import aiohttp
from hashlib import md5

groups = {
    0: "undefined", 1: "8А", 2: "8В", 3: "9В", 4: "9А", 5: "9Б", 6: "11А", 7: "11Б", 8: "11В", 9: "9Е", 11: "9Г",
    12: "10А", 13: "10Б", 14: "10В", 15: "10Г", 16: "10Д", 17: "10Е", 18: "10З", 19: "10К", 20: "10Л", 21: "10М",
    22: "10Н", 23: "10С", 24: "11Г", 25: "11Д", 26: "11Е", 27: "11З", 28: "11К", 29: "11Л", 30: "11М", 31: "11С",
    32: "11Н"
}
groups_inverse = {
    "undefined": 0, "8А": 1, "8В": 2, "9В": 3, "9А": 4, "9Б": 5, "11А": 6, "11Б": 7, "11В": 8, "9Е": 9, "9Г": 11,
    "10А": 12, "10Б": 13, "10В": 14, "10Г": 15, "10Д": 16, "10Е": 17, "10З": 18, "10К": 19, "10Л": 20, "10М": 21,
    "10Н": 22, "10С": 23, "11Г": 24, "11Д": 25, "11Е": 26, "11З": 27, "11К": 28, "11Л": 29, "11М": 30, "11С": 31,
    "11Н": 32
}


def group_name_by_id(group_id):
    return groups[group_id]


def id_by_group_name(group_name):
    return groups_inverse[group_name]


def group_id_exists(group_id):
    return group_id in groups


def group_name_exists(group_name):
    return group_name in groups_inverse


@dataclass(eq=True, frozen=True)
class Lesson:
    subject: str
    auditory: str
    group: int
    subgroup: int
    teacher: str
    number: int
    is_diff: bool

    @staticmethod
    def from_json(d, is_diff=False):
        try:
            return Lesson(d["subject"], d["auditory"], id_by_group_name(d["group"]),
                          d["subgroup"], d["teacher"], d["number"], is_diff)
        except KeyError:
            raise ValueError("Missed required lesson parameters")


class LessonPool:
    def __init__(self):
        self.by_group = defaultdict(set)
        self.by_teacher = defaultdict(set)
        self.by_auditory = defaultdict(set)

    def add(self, lesson: Lesson):
        self.by_group[lesson.group].add(lesson)
        self.by_teacher[lesson.teacher].add(lesson)
        self.by_auditory[lesson.auditory].add(lesson)

    def remove(self, lesson: Lesson):
        self.by_group[lesson.group].remove(lesson)
        self.by_teacher[lesson.teacher].remove(lesson)
        self.by_auditory[lesson.auditory].remove(lesson)

    def for_group(self, group):
        return self.by_group[group]

    def for_teacher(self, teacher):
        return self.by_teacher[teacher]

    def for_auditory(self, auditory):
        return self.by_auditory[auditory]

    def merge(self, other_pool):
        for lesson in other_pool:
            self.add(lesson)

    def __contains__(self, lesson):
        return lesson in self.by_group[lesson.group]

    class Iterator:
        def __init__(self, pool):
            self.pool = pool
            self.group_iter = iter(pool.by_group)
            try:
                self.lesson_iter = iter(pool.by_group[next(self.group_iter)])
            except StopIteration:
                self.lesson_iter = None

        def __next__(self):
            if self.lesson_iter is None:
                raise StopIteration

            while True:
                try:
                    return next(self.lesson_iter)
                except StopIteration:
                    self.lesson_iter = iter(self.pool.by_group[next(self.group_iter)])

    def __iter__(self):
        return LessonPool.Iterator(self)


SyncReport = namedtuple("SyncReport", ["cached", "added", "removed"])
SyncStats = namedtuple("SyncStats", ["synced", "cached", "errored"], defaults=(0, 0, 0))


class ScheduleDay(LessonPool):
    def __init__(self, weekday: int):
        super().__init__()

        self.weekday = weekday
        self.sync_hash = defaultdict(str)

    async def __sync_group(self, group, session: aiohttp.ClientSession) -> SyncReport:
        url = f"https://lyceum.urfu.ru/?type=11&scheduleType=group&weekday={self.weekday + 1}&group={group}"
        async with session.get(url) as response:
            data = await response.text()

        hash_ = md5(data.encode()).hexdigest()
        if self.sync_hash[group] == hash_:
            return SyncReport(cached=True, added=None, removed=None)

        self.sync_hash[group] = hash_
        data = json.loads(data)

        diffed = set()
        to_add = LessonPool()
        to_remove = LessonPool()

        for entry in data["diffs"]:
            lesson = Lesson.from_json(entry, is_diff=True)
            diffed.add(lesson.number)
            to_add.add(lesson)

        for entry in data["lessons"]:
            lesson = Lesson.from_json(entry)
            if lesson.number not in diffed:
                to_add.add(lesson)

        for lesson in self.for_group(group):
            if lesson in to_add:
                to_add.remove(lesson)
            else:
                to_remove.add(lesson)

        for lesson in to_add:
            self.add(lesson)

        for lesson in to_remove:
            self.remove(lesson)

        return SyncReport(cached=False, added=to_add, removed=to_remove)

    # TODO: measure stats
    async def sync(self):
        diffs_added, diffs_removed = LessonPool(), LessonPool()

        async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=False)) as session:
            for result in await asyncio.gather(
                    *[self.__sync_group(group, session) for group in groups], return_exceptions=True):
                if isinstance(result, SyncReport):
                    if result.cached:
                        pass
                        # stats.cached += 1
                    else:
                        # stats.synced += 1
                        diffs_added.merge(result.added)
                        diffs_removed.merge(result.removed)
                elif isinstance(result, BaseException):
                    # stats.errored += 1

                    # TODO: We filter JSONDecodeError caused by empty response,
                    #       but it'll be better to check it on receive.
                    if not isinstance(result, json.JSONDecodeError):
                        logging.error("Sync exception:")

                        # backward compatibility for 3.9
                        # https://docs.python.org/3/library/traceback.html#traceback.print_exception
                        traceback.print_exception(..., result, result.__traceback__)

        return diffs_added, diffs_removed


class ScheduleProvider:
    def __init__(self):
        self.week = [ScheduleDay(day) for day in range(7)]

    async def sync_day(self, day):
        return await self.week[day].sync()

    def for_group(self, group, day, week=None):
        return self.week[day].for_group(group)

    def for_teacher(self, teacher, day, week=None):
        return self.week[day].for_teacher(teacher)

    def for_auditory(self, auditory, day, week=None):
        return self.week[day].for_auditory(auditory)
