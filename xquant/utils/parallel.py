# -*- coding: utf-8 -*-

"""
通过multiprocessing模块将串行计算变成并行计算的框架
使用concurrent和synchronized两个装饰器实现并行计算

Credit: Alex Sherman
Ref: https://github.com/alex-sherman/deco

缺陷：代码不符合PEP8

#################################
# 示例1
#################################
from xquant.utils.parallel import *
import time

@concurrent
def work():
    time.sleep(0.1)


@synchronized
def run():
    for _ in range(100):
        work()


if __name__ == "__main__":
    start = time.time()
    run()
    print("Executing in serial should take 10 seconds")
    print("Executing in parallel took:", time.time() - start, "seconds")

###################################
# 示例2
###################################
from xquant.utils.parallel import *
import time
import random
from collections import defaultdict


@concurrent  # We add this for the concurrent function
def process_lat_lon(lat, lon, data):
    time.sleep(0.1)
    return data[lat + lon]


@synchronized  # And we add this for the function which calls the concurrent function
def process_data_set(data):
    results = defaultdict(dict)
    for lat in range(5):
        for lon in range(5):
            results[lat][lon] = process_lat_lon(lat, lon, data)
    return dict(results)

if __name__ == "__main__":
    random.seed(0)
    data = [random.random() for _ in range(200)]
    start = time.time()
    print(process_data_set(data))
    print(time.time() - start)

##########################################
更多例子参考
Ref: https://github.com/alex-sherman/deco
##########################################
"""
import ast
from ast import NodeTransformer
import sys
import types
import inspect

from multiprocessing import Pool
from multiprocessing.pool import ThreadPool


def unindent(source_lines):
    for i, line in enumerate(source_lines):
        source_lines[i] = line.lstrip()
        if source_lines[i][:3] == "def":
            break

def Call(func, args=None, kwargs=None):
    if args is None:
        args = []
    if kwargs is None:
        kwargs = []
    if sys.version_info >= (3, 5):
        return ast.Call(func, args, kwargs)
    else:
        return ast.Call(func, args, kwargs, None, None)


class SchedulerRewriter(NodeTransformer):
    def __init__(self, concurrent_funcs):
        self.arguments = set()
        self.concurrent_funcs = concurrent_funcs
        self.encountered_funcs = set()

    def references_arg(self, node):
        if not isinstance(node, ast.AST):
            return False
        if type(node) is ast.Name:
            return type(node.ctx) is ast.Load and node.id in self.arguments
        for field in node._fields:
            if field == "body": continue
            value = getattr(node, field)
            if not hasattr(value, "__iter__"):
                value = [value]
            if any([self.references_arg(child) for child in value]):
                return True
        return False

    @staticmethod
    def top_level_name(node):
        if type(node) is ast.Name:
            return node.id
        elif type(node) is ast.Subscript or type(node) is ast.Attribute:
            return SchedulerRewriter.top_level_name(node.value)
        return None

    def is_concurrent_call(self, node):
        return type(node) is ast.Call and type(node.func) is ast.Name and node.func.id in self.concurrent_funcs

    def is_valid_assignment(self, node):
        if not (type(node) is ast.Assign and self.is_concurrent_call(node.value)):
            return False
        if len(node.targets) != 1:
            raise ValueError("并发不支持多个赋值对象")
        if not type(node.targets[0]) is ast.Subscript:
            raise ValueError("并发只支持可索引对象")
        return True

    def encounter_call(self, call):
        self.encountered_funcs.add(call.func.id)
        for arg in call.args:
            arg_name = SchedulerRewriter.top_level_name(arg)
            if arg_name is not None:
                self.arguments.add(arg_name)

    def generic_visit(self, node):
        super(NodeTransformer, self).generic_visit(node)
        if hasattr(node, 'body') and type(node.body) is list:
            returns = [i for i, child in enumerate(node.body) if type(child) is ast.Return]
            if len(returns) > 0:
                for wait in self.get_waits():
                    node.body.insert(returns[0], wait)
            inserts = []
            for i, child in enumerate(node.body):
                if type(child) is ast.Expr and self.is_concurrent_call(child.value):
                    self.encounter_call(child.value)
                elif self.is_valid_assignment(child):
                    call = child.value
                    self.encounter_call(call)
                    name = child.targets[0].value
                    self.arguments.add(SchedulerRewriter.top_level_name(name))
                    index = child.targets[0].slice.value
                    call.func = ast.Attribute(call.func, 'assign', ast.Load())
                    call.args = [ast.Tuple([name, index], ast.Load())] + call.args
                    node.body[i] = ast.Expr(call)
                elif self.references_arg(child):
                    inserts.insert(0, i)
            for index in inserts:
                for wait in self.get_waits():
                    node.body.insert(index, wait)

    def get_waits(self):
        return [ast.Expr(Call(ast.Attribute(ast.Name(fname, ast.Load()),
                                            'wait', ast.Load()))) for fname in self.encountered_funcs]

    def visit_FunctionDef(self, node):
        node.decorator_list = []
        self.generic_visit(node)
        node.body += self.get_waits()
        return node


def concWrapper(f, args, kwargs):
    result = concurrent.functions[f](*args, **kwargs)
    operations = [inner for outer in args + list(kwargs.values())
                  if type(outer) is argProxy for inner in outer.operations]
    return result, operations


class argProxy(object):
    def __init__(self, arg_id, value):
        self.arg_id = arg_id
        self.operations = []
        self.value = value

    def __getattr__(self, name):
        if name in ["__getstate__", "__setstate__"]:
            raise AttributeError
        if hasattr(self, 'value') and hasattr(self.value, name):
            return getattr(self.value, name)
        raise AttributeError

    def __setitem__(self, key, value):
        self.value.__setitem__(key, value)
        self.operations.append((self.arg_id, key, value))

    def __getitem__(self, key):
        return self.value.__getitem__(key)


class synchronized(object):
    def __init__(self, f):
        self.orig_f = f
        self.f = None
        self.ast = None

    def __get__(self, *args):
        raise NotImplementedError("并行装饰器不可用于类方法")

    def __call__(self, *args, **kwargs):
        if self.f is None:
            source = inspect.getsourcelines(self.orig_f)[0]
            unindent(source)
            source = "".join(source)
            self.ast = ast.parse(source)
            rewriter = SchedulerRewriter(concurrent.functions.keys())
            rewriter.visit(self.ast.body[0])
            ast.fix_missing_locations(self.ast)
            out = compile(self.ast, "<string>", "exec")
            scope = dict(self.orig_f.__globals__)
            exec(out, scope)
            self.f = scope[self.orig_f.__name__]
        return self.f(*args, **kwargs)


class concurrent(object):
    functions = {}

    @staticmethod
    def custom(constructor = None, apply_async = None):
        @staticmethod
        def _custom_concurrent(*args, **kwargs):
            conc = concurrent(*args, **kwargs)
            if constructor is not None: conc.conc_constructor = constructor
            if apply_async is not None: conc.apply_async = apply_async
            return conc
        return _custom_concurrent

    def __init__(self, *args, **kwargs):
        self.in_progress = False
        self.conc_args = []
        self.conc_kwargs = {}
        if len(args) > 0 and isinstance(args[0], types.FunctionType):
            self.setFunction(args[0])
        else:
            self.conc_args = args
            self.conc_kwargs = kwargs
        self.results = []
        self.assigns = []
        self.arg_proxies = {}
        self.conc_constructor = Pool
        self.apply_async = lambda self, function, args: self.concurrency.apply_async(function, args)
        self.concurrency = None

    def __get__(self, *args):
        raise NotImplementedError("并行装饰器不可用于类方法")

    def replaceWithProxies(self, args):
        args_iter = args.items() if type(args) is dict else enumerate(args)
        for i, arg in args_iter:
            if type(arg) is dict or type(arg) is list:
                if not id(arg) in self.arg_proxies:
                    self.arg_proxies[id(arg)] = argProxy(id(arg), arg)
                args[i] = self.arg_proxies[id(arg)]

    def setFunction(self, f):
        concurrent.functions[f.__name__] = f
        self.f_name = f.__name__

    def assign(self, target, *args, **kwargs):
        self.assigns.append((target, self(*args, **kwargs)))

    def __call__(self, *args, **kwargs):
        if len(args) > 0 and isinstance(args[0], types.FunctionType):
            self.setFunction(args[0])
            return self
        self.in_progress = True
        if self.concurrency is None:
            self.concurrency = self.conc_constructor(*self.conc_args, **self.conc_kwargs)
        args = list(args)
        self.replaceWithProxies(args)
        self.replaceWithProxies(kwargs)
        result = ConcurrentResult(self, self.apply_async(self, concWrapper, [self.f_name, args, kwargs]))
        self.results.append(result)
        return result

    def apply_operations(self, ops):
        for arg_id, key, value in ops:
            self.arg_proxies[arg_id].value.__setitem__(key, value)

    def wait(self):
        results = []
        while len(self.results) > 0:
            results.append(self.results.pop().get())
        for assign in self.assigns:
            assign[0][0][assign[0][1]] = assign[1].get()
        self.assigns = []
        self.arg_proxies = {}
        self.in_progress = False
        return results

concurrent.threaded = concurrent.custom(ThreadPool)


class ConcurrentResult(object):
    def __init__(self, decorator, async_result):
        self.decorator = decorator
        self.async_result = async_result

    def get(self):
        result, operations = self.async_result.get()
        self.decorator.apply_operations(operations)
        return result


__all__ = ['concurrent', 'synchronized']