# -*- coding: utf-8 -*-

"""
性能分析或优化相关的功能
主要用于对策略的运算性能瓶颈（bottlenecks）做简单分析

其他可选的库如：line_profiler, cProfile, timeit等

Credit: Bryan Helmig (inspiration), Robert Kern (line_profiler) and more

@author: Leon Zhang
"""

import time
import cProfile


def time_func(f):
    """
    实现一个对函数运行时间计时的简单装饰器（decorator）
    参数：
    f: 需要进行运行时间分析的函数

    使用示例：
    @time_func
    def expensive_function():
        for x in range(10000):
            _ = x ** x
        return 'OK!'

    result = expensive_function()
    """
    def f_timer(*args, **kwargs):
        start = time.time()
        result = f(*args, **kwargs)
        end = time.time()
        print(f.__name__, 'took', end - start, 'seconds!')
        return result
    return f_timer


class TimeWith(object):
    """
    计时的上下文管理器（context manager）
    用例：
    方法1：with...as的上下文管理方法
    with TimeWith('Test') as timer:
        expensive_function()
        timer.checkpoint('run once')
        expensive_function()
        expensive_function()
        timer.checkpoint('run twice again')
    方法2：直接使用
    timer = TimeWith('测试')
    expensive_function()
    timer.checkpoint('跑了一次')
    """
    def __init__(self, name=''):
        self.name = name
        self.start = time.time()

    @property
    def duration(self):
        return time.time() - self.start

    def checkpoint(self, name=''):
        print('{timer} {checkpoint} took {elapsed} seconds'.format(
            timer=self.name, checkpoint=name, elapsed=self.duration).strip())

    def __enter__(self):
        return self

    def __exit__(self, exc_type, value, traceback):
        self.checkpoint('finished')


def do_cprofile(func):
    """
    使用内置的cProfile模块实现性能分析装饰器
    用例：
    @do_cprofile
    def expensive_function():
        for x in range(10000):
            _ = x ** x
        return 'OK!'

    result = expensive_function()
    """
    def profiled_func(*args, **kwargs):
        profile = cProfile.Profile()
        try:
            profile.enable()
            result = func(*args, **kwargs)
            profile.disable()
            return result
        finally:
            profile.print_stats()
    return profiled_func


try:
    from line_profiler import LineProfiler

    def do_profile(follow=None):
        """
        使用line_profiler创建性能分析装饰器
        follow列表选择要追踪的函数，如果为空，则全部分析
        用例：
        def num_range(n):
            for x in range(n):
                yield x

        @do_profile(follow=[num_range])
        def expensive_function():
            for x in num_range(1000):
                _ = x ** x
            return 'OK!'

        result = expensive_function()
        """
        if follow is None:
            follow = list()
        def inner(func):
            def profiled_func(*args, **kwargs):
                profiler = LineProfiler()
                try:
                    profiler.add_function(func)
                    for f in follow:
                        profiler.add_function(f)
                    profiler.enable_by_count()
                    return func(*args, **kwargs)
                finally:
                    profiler.print_stats()
            return profiled_func
        return inner

except ImportError:
    def do_profile(follow=None):
        """
        line_profile未安装情况下的备选装饰器，什么也不做
        """
        def inner(func):
            def nothing(*args, **kwargs):
                return func(*args, **kwargs)
            return nothing
        return inner


if __name__ == '__main__':
    def expensive_function():
        for x in range(10000):
            _ = x ** x
        return 'OK!'

    with TimeWith('Test') as timer:
        expensive_function()
        timer.checkpoint('run once')
        expensive_function()
        expensive_function()
        timer.checkpoint('run twice again')