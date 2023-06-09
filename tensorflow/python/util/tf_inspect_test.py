# Copyright 2017 The TensorFlow Authors. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ==============================================================================
"""Unit tests for tf_inspect."""

# pylint: disable=unused-import
import functools
import inspect

from tensorflow.python.platform import test
from tensorflow.python.platform import tf_logging as logging
from tensorflow.python.util import tf_decorator
from tensorflow.python.util import tf_inspect


def test_decorator(decorator_name, decorator_doc=None):

  def make_tf_decorator(target):
    return tf_decorator.TFDecorator(decorator_name, target, decorator_doc)

  return make_tf_decorator


def test_undecorated_function():
  pass


@test_decorator('decorator 1')
@test_decorator('decorator 2')
@test_decorator('decorator 3')
def test_decorated_function(x):
  """Test Decorated Function Docstring."""
  return x * 2


@test_decorator('decorator')
def test_decorated_function_with_defaults(a, b=2, c='Hello'):
  """Test Decorated Function With Defaults Docstring."""
  return [a, b, c]


@test_decorator('decorator')
def test_decorated_function_with_varargs_and_kwonlyargs(*args, b=2, c='Hello'):
  """Test Decorated Function With both varargs and keyword args."""
  return [args, b, c]


@test_decorator('decorator')
class TestDecoratedClass(object):
  """Test Decorated Class."""

  def __init__(self):
    pass

  def two(self):
    return 2


class TfInspectTest(test.TestCase):

  def testCurrentFrame(self):
    self.assertEqual(inspect.currentframe(), tf_inspect.currentframe())

  def testGetArgSpecOnDecoratorsThatDontProvideArgspec(self):
    argspec = tf_inspect.getargspec(test_decorated_function_with_defaults)
    self.assertEqual(['a', 'b', 'c'], argspec.args)
    self.assertEqual((2, 'Hello'), argspec.defaults)

  def testGetArgSpecOnDecoratorThatChangesArgspec(self):
    argspec = tf_inspect.FullArgSpec(
        args=['a', 'b', 'c'],
        varargs=None,
        varkw=None,
        defaults=(1, 'hello'),
        kwonlyargs=[],
        kwonlydefaults=None,
        annotations={},
    )

    decorator = tf_decorator.TFDecorator('', test_undecorated_function, '',
                                         argspec)
    self.assertEqual(argspec, tf_inspect.getfullargspec(decorator))

  def testGetArgSpecIgnoresDecoratorsThatDontProvideArgspec(self):
    argspec = tf_inspect.FullArgSpec(
        args=['a', 'b', 'c'],
        varargs=None,
        varkw=None,
        defaults=(1, 'hello'),
        kwonlyargs=[],
        kwonlydefaults=None,
        annotations={},
    )

    inner_decorator = tf_decorator.TFDecorator(
        '', test_undecorated_function, '', argspec
    )
    outer_decorator = tf_decorator.TFDecorator('', inner_decorator)
    self.assertEqual(argspec, tf_inspect.getargspec(outer_decorator))

  def testGetArgSpecThatContainsVarargsAndKwonlyArgs(self):
    argspec = tf_inspect.getargspec(
        test_decorated_function_with_varargs_and_kwonlyargs
    )
    self.assertEqual(['b', 'c'], argspec.args)
    self.assertEqual((2, 'Hello'), argspec.defaults)

  def testGetArgSpecReturnsOutermostDecoratorThatChangesArgspec(self):
    outer_argspec = tf_inspect.FullArgSpec(
        args=['a'],
        varargs=None,
        varkw=None,
        defaults=(),
        kwonlyargs=[],
        kwonlydefaults=None,
        annotations={},
    )
    inner_argspec = tf_inspect.FullArgSpec(
        args=['b'],
        varargs=None,
        varkw=None,
        defaults=(),
        kwonlyargs=[],
        kwonlydefaults=None,
        annotations={},
    )

    inner_decorator = tf_decorator.TFDecorator('', test_undecorated_function,
                                               '', inner_argspec)
    outer_decorator = tf_decorator.TFDecorator('', inner_decorator, '',
                                               outer_argspec)
    self.assertEqual(outer_argspec, tf_inspect.getfullargspec(outer_decorator))

  def testGetArgSpecOnPartialPositionalArgumentOnly(self):
    """Tests getargspec on partial function with only positional arguments."""

    def func(m, n):
      return 2 * m + n

    partial_func = functools.partial(func, 7)
    argspec = tf_inspect.ArgSpec(
        args=['n'], varargs=None, keywords=None, defaults=None)

    self.assertEqual(argspec, tf_inspect.getargspec(partial_func))

  def testGetArgSpecOnPartialArgumentWithConvertibleToFalse(self):
    """Tests getargspec on partial function with args that convert to False."""

    def func(m, n):
      return 2 * m + n

    partial_func = functools.partial(func, m=0)

    with self.assertRaisesRegex(ValueError, 'keyword-only arguments'):
      tf_inspect.getargspec(partial_func)

  def testGetArgSpecOnPartialInvalidArgspec(self):
    """Tests getargspec on partial function that doesn't have valid argspec."""

    def func(m, n, l, k=4):
      return 2 * m + l + n * k

    partial_func = functools.partial(func, n=7)

    with self.assertRaisesRegex(ValueError, 'keyword-only arguments'):
      tf_inspect.getargspec(partial_func)

  def testGetArgSpecOnPartialValidArgspec(self):
    """Tests getargspec on partial function with valid argspec."""

    def func(m, n, l, k=4):
      return 2 * m + l + n * k

    partial_func = functools.partial(func, n=7, l=2)
    argspec = tf_inspect.ArgSpec(
        args=['m', 'n', 'l', 'k'],
        varargs=None,
        keywords=None,
        defaults=(7, 2, 4))

    self.assertEqual(argspec, tf_inspect.getargspec(partial_func))

  def testGetArgSpecOnPartialNoArgumentsLeft(self):
    """Tests getargspec on partial function that prunes all arguments."""

    def func(m, n):
      return 2 * m + n

    partial_func = functools.partial(func, 7, 10)
    argspec = tf_inspect.ArgSpec(
        args=[], varargs=None, keywords=None, defaults=None)

    self.assertEqual(argspec, tf_inspect.getargspec(partial_func))

  def testGetArgSpecOnPartialKeywordArgument(self):
    """Tests getargspec on partial function that prunes some arguments."""

    def func(m, n):
      return 2 * m + n

    partial_func = functools.partial(func, n=7)
    argspec = tf_inspect.ArgSpec(
        args=['m', 'n'], varargs=None, keywords=None, defaults=(7,))

    self.assertEqual(argspec, tf_inspect.getargspec(partial_func))

  def testGetArgSpecOnPartialKeywordArgumentWithDefaultValue(self):
    """Tests getargspec on partial function that prunes argument by keyword."""

    def func(m=1, n=2):
      return 2 * m + n

    partial_func = functools.partial(func, n=7)
    argspec = tf_inspect.ArgSpec(
        args=['m', 'n'], varargs=None, keywords=None, defaults=(1, 7))

    self.assertEqual(argspec, tf_inspect.getargspec(partial_func))

  def testGetArgSpecOnPartialWithVarargs(self):
    """Tests getargspec on partial function with variable arguments."""

    def func(m, *arg):
      return m + len(arg)

    partial_func = functools.partial(func, 7, 8)
    argspec = tf_inspect.ArgSpec(
        args=[], varargs='arg', keywords=None, defaults=None)

    self.assertEqual(argspec, tf_inspect.getargspec(partial_func))

  def testGetArgSpecOnPartialWithVarkwargs(self):
    """Tests getargspec on partial function with variable keyword arguments."""

    def func(m, n, **kwarg):
      return m * n + len(kwarg)

    partial_func = functools.partial(func, 7)
    argspec = tf_inspect.ArgSpec(
        args=['n'], varargs=None, keywords='kwarg', defaults=None)

    self.assertEqual(argspec, tf_inspect.getargspec(partial_func))

  def testGetArgSpecOnPartialWithDecorator(self):
    """Tests getargspec on decorated partial function."""

    @test_decorator('decorator')
    def func(m=1, n=2):
      return 2 * m + n

    partial_func = functools.partial(func, n=7)
    argspec = tf_inspect.ArgSpec(
        args=['m', 'n'], varargs=None, keywords=None, defaults=(1, 7))

    self.assertEqual(argspec, tf_inspect.getargspec(partial_func))

  def testGetArgSpecOnPartialWithDecoratorThatChangesArgspec(self):
    """Tests getargspec on partial function with decorated argspec."""

    argspec = tf_inspect.FullArgSpec(
        args=['a', 'b', 'c'],
        varargs=None,
        varkw=None,
        defaults=(1, 'hello'),
        kwonlyargs=[],
        kwonlydefaults=None,
        annotations={},
    )
    decorator = tf_decorator.TFDecorator('', test_undecorated_function, '',
                                         argspec)
    signature = inspect.Signature([
        inspect.Parameter(
            'a', inspect.Parameter.KEYWORD_ONLY, default=2
        ),
        inspect.Parameter(
            'b', inspect.Parameter.KEYWORD_ONLY, default=1
        ),
        inspect.Parameter(
            'c', inspect.Parameter.KEYWORD_ONLY, default='hello'
        ),
    ])
    partial_with_decorator = functools.partial(decorator, a=2)
    self.assertEqual(argspec, tf_inspect.getfullargspec(decorator))
    self.assertEqual(signature, inspect.signature(partial_with_decorator))

  def testGetArgSpecOnCallableObject(self):

    class Callable(object):

      def __call__(self, a, b=1, c='hello'):
        pass

    argspec = tf_inspect.ArgSpec(
        args=['self', 'a', 'b', 'c'],
        varargs=None,
        keywords=None,
        defaults=(1, 'hello'))

    test_obj = Callable()
    self.assertEqual(argspec, tf_inspect.getargspec(test_obj))

  def testGetArgSpecOnInitClass(self):

    class InitClass(object):

      def __init__(self, a, b=1, c='hello'):
        pass

    argspec = tf_inspect.ArgSpec(
        args=['self', 'a', 'b', 'c'],
        varargs=None,
        keywords=None,
        defaults=(1, 'hello'))

    self.assertEqual(argspec, tf_inspect.getargspec(InitClass))

  def testGetArgSpecOnNewClass(self):

    class NewClass(object):

      def __new__(cls, a, b=1, c='hello'):
        pass

    argspec = tf_inspect.ArgSpec(
        args=['cls', 'a', 'b', 'c'],
        varargs=None,
        keywords=None,
        defaults=(1, 'hello'))

    self.assertEqual(argspec, tf_inspect.getargspec(NewClass))

  def testGetFullArgSpecOnDecoratorsThatDontProvideFullArgSpec(self):
    argspec = tf_inspect.getfullargspec(test_decorated_function_with_defaults)
    self.assertEqual(['a', 'b', 'c'], argspec.args)
    self.assertEqual((2, 'Hello'), argspec.defaults)

  def testGetFullArgSpecOnDecoratorThatChangesFullArgSpec(self):
    argspec = tf_inspect.FullArgSpec(
        args=['a', 'b', 'c'],
        varargs=None,
        varkw=None,
        defaults=(1, 'hello'),
        kwonlyargs=[],
        kwonlydefaults=None,
        annotations={})

    decorator = tf_decorator.TFDecorator('', test_undecorated_function, '',
                                         argspec)
    self.assertEqual(argspec, tf_inspect.getfullargspec(decorator))

  def testGetFullArgSpecIgnoresDecoratorsThatDontProvideFullArgSpec(self):
    argspec = tf_inspect.FullArgSpec(
        args=['a', 'b', 'c'],
        varargs=None,
        varkw=None,
        defaults=(1, 'hello'),
        kwonlyargs=[],
        kwonlydefaults=None,
        annotations={})

    inner_decorator = tf_decorator.TFDecorator('', test_undecorated_function,
                                               '', argspec)
    outer_decorator = tf_decorator.TFDecorator('', inner_decorator)
    self.assertEqual(argspec, tf_inspect.getfullargspec(outer_decorator))

  def testGetFullArgSpecReturnsOutermostDecoratorThatChangesFullArgSpec(self):
    outer_argspec = tf_inspect.FullArgSpec(
        args=['a'],
        varargs=None,
        varkw=None,
        defaults=None,
        kwonlyargs=[],
        kwonlydefaults=None,
        annotations={})
    inner_argspec = tf_inspect.FullArgSpec(
        args=['b'],
        varargs=None,
        varkw=None,
        defaults=None,
        kwonlyargs=[],
        kwonlydefaults=None,
        annotations={})

    inner_decorator = tf_decorator.TFDecorator('', test_undecorated_function,
                                               '', inner_argspec)
    outer_decorator = tf_decorator.TFDecorator('', inner_decorator, '',
                                               outer_argspec)
    self.assertEqual(outer_argspec, tf_inspect.getfullargspec(outer_decorator))

  def testGetFullArgsSpecForPartial(self):

    def func(a, b):
      del a, b

    partial_function = functools.partial(func, 1)
    argspec = tf_inspect.FullArgSpec(
        args=['b'],
        varargs=None,
        varkw=None,
        defaults=None,
        kwonlyargs=[],
        kwonlydefaults=None,
        annotations={})

    self.assertEqual(argspec, tf_inspect.getfullargspec(partial_function))

  def testGetFullArgSpecOnPartialNoArgumentsLeft(self):
    """Tests getfullargspec on partial function that prunes all arguments."""

    def func(m, n):
      return 2 * m + n

    partial_func = functools.partial(func, 7, 10)
    argspec = tf_inspect.FullArgSpec(
        args=[],
        varargs=None,
        varkw=None,
        defaults=None,
        kwonlyargs=[],
        kwonlydefaults=None,
        annotations={})

    self.assertEqual(argspec, tf_inspect.getfullargspec(partial_func))

  def testGetFullArgSpecOnPartialWithVarargs(self):
    """Tests getfullargspec on partial function with variable arguments."""

    def func(m, *arg):
      return m + len(arg)

    partial_func = functools.partial(func, 7, 8)
    argspec = tf_inspect.FullArgSpec(
        args=[],
        varargs='arg',
        varkw=None,
        defaults=None,
        kwonlyargs=[],
        kwonlydefaults=None,
        annotations={})

    self.assertEqual(argspec, tf_inspect.getfullargspec(partial_func))

  def testGetFullArgSpecOnPartialWithVarkwargs(self):
    """Tests getfullargspec.

    Tests on partial function with variable keyword arguments.
    """

    def func(m, n, **kwarg):
      return m * n + len(kwarg)

    partial_func = functools.partial(func, 7)
    argspec = tf_inspect.FullArgSpec(
        args=['n'],
        varargs=None,
        varkw='kwarg',
        defaults=None,
        kwonlyargs=[],
        kwonlydefaults=None,
        annotations={})

    self.assertEqual(argspec, tf_inspect.getfullargspec(partial_func))

  def testGetFullArgSpecOnCallableObject(self):

    class Callable(object):

      def __call__(self, a, b=1, c='hello'):
        pass

    argspec = tf_inspect.FullArgSpec(
        args=['self', 'a', 'b', 'c'],
        varargs=None,
        varkw=None,
        defaults=(1, 'hello'),
        kwonlyargs=[],
        kwonlydefaults=None,
        annotations={})

    test_obj = Callable()
    self.assertEqual(argspec, tf_inspect.getfullargspec(test_obj))

  def testGetFullArgSpecOnInitClass(self):

    class InitClass(object):

      def __init__(self, a, b=1, c='hello'):
        pass

    argspec = tf_inspect.FullArgSpec(
        args=['self', 'a', 'b', 'c'],
        varargs=None,
        varkw=None,
        defaults=(1, 'hello'),
        kwonlyargs=[],
        kwonlydefaults=None,
        annotations={})

    self.assertEqual(argspec, tf_inspect.getfullargspec(InitClass))

  def testGetFullArgSpecOnNewClass(self):

    class NewClass(object):

      def __new__(cls, a, b=1, c='hello'):
        pass

    argspec = tf_inspect.FullArgSpec(
        args=['cls', 'a', 'b', 'c'],
        varargs=None,
        varkw=None,
        defaults=(1, 'hello'),
        kwonlyargs=[],
        kwonlydefaults=None,
        annotations={})

    self.assertEqual(argspec, tf_inspect.getfullargspec(NewClass))

  def testSignatureOnDecoratorsThatDontProvideFullArgSpec(self):
    signature = tf_inspect.signature(test_decorated_function_with_defaults)

    self.assertEqual([
        tf_inspect.Parameter('a', tf_inspect.Parameter.POSITIONAL_OR_KEYWORD),
        tf_inspect.Parameter(
            'b', tf_inspect.Parameter.POSITIONAL_OR_KEYWORD, default=2),
        tf_inspect.Parameter(
            'c', tf_inspect.Parameter.POSITIONAL_OR_KEYWORD, default='Hello')
    ], list(signature.parameters.values()))

  def testSignatureFollowsNestedDecorators(self):
    signature = tf_inspect.signature(test_decorated_function)

    self.assertEqual(
        [tf_inspect.Parameter('x', tf_inspect.Parameter.POSITIONAL_OR_KEYWORD)],
        list(signature.parameters.values()))

  def testGetDoc(self):
    self.assertEqual('Test Decorated Function With Defaults Docstring.',
                     tf_inspect.getdoc(test_decorated_function_with_defaults))

  def testGetFile(self):
    self.assertTrue('tf_inspect_test.py' in tf_inspect.getfile(
        test_decorated_function_with_defaults))
    self.assertTrue('tf_decorator.py' in tf_inspect.getfile(
        test_decorator('decorator')(tf_decorator.unwrap)))

  def testGetMembers(self):
    self.assertEqual(
        inspect.getmembers(TestDecoratedClass),
        tf_inspect.getmembers(TestDecoratedClass))

  def testGetModule(self):
    self.assertEqual(
        inspect.getmodule(TestDecoratedClass),
        tf_inspect.getmodule(TestDecoratedClass))
    self.assertEqual(
        inspect.getmodule(test_decorated_function),
        tf_inspect.getmodule(test_decorated_function))
    self.assertEqual(
        inspect.getmodule(test_undecorated_function),
        tf_inspect.getmodule(test_undecorated_function))

  def testGetSource(self):
    expected = '''@test_decorator('decorator')
def test_decorated_function_with_defaults(a, b=2, c='Hello'):
  """Test Decorated Function With Defaults Docstring."""
  return [a, b, c]
'''
    self.assertEqual(
        expected, tf_inspect.getsource(test_decorated_function_with_defaults))

  def testGetSourceFile(self):
    self.assertEqual(
        __file__,
        tf_inspect.getsourcefile(test_decorated_function_with_defaults))

  def testGetSourceLines(self):
    expected = inspect.getsourcelines(
        test_decorated_function_with_defaults.decorated_target)
    self.assertEqual(
        expected,
        tf_inspect.getsourcelines(test_decorated_function_with_defaults))

  def testIsBuiltin(self):
    self.assertEqual(
        tf_inspect.isbuiltin(TestDecoratedClass),
        inspect.isbuiltin(TestDecoratedClass))
    self.assertEqual(
        tf_inspect.isbuiltin(test_decorated_function),
        inspect.isbuiltin(test_decorated_function))
    self.assertEqual(
        tf_inspect.isbuiltin(test_undecorated_function),
        inspect.isbuiltin(test_undecorated_function))
    self.assertEqual(tf_inspect.isbuiltin(range), inspect.isbuiltin(range))
    self.assertEqual(tf_inspect.isbuiltin(max), inspect.isbuiltin(max))

  def testIsClass(self):
    self.assertTrue(tf_inspect.isclass(TestDecoratedClass))
    self.assertFalse(tf_inspect.isclass(test_decorated_function))

  def testIsFunction(self):
    self.assertTrue(tf_inspect.isfunction(test_decorated_function))
    self.assertFalse(tf_inspect.isfunction(TestDecoratedClass))

  def testIsMethod(self):
    self.assertTrue(tf_inspect.ismethod(TestDecoratedClass().two))
    self.assertFalse(tf_inspect.ismethod(test_decorated_function))

  def testIsModule(self):
    self.assertTrue(
        tf_inspect.ismodule(inspect.getmodule(inspect.currentframe())))
    self.assertFalse(tf_inspect.ismodule(test_decorated_function))

  def testIsRoutine(self):
    self.assertTrue(tf_inspect.isroutine(len))
    self.assertFalse(tf_inspect.isroutine(TestDecoratedClass))

  def testStack(self):
    expected_stack = inspect.stack()
    actual_stack = tf_inspect.stack()
    self.assertEqual(len(expected_stack), len(actual_stack))
    self.assertEqual(expected_stack[0][0], actual_stack[0][0])  # Frame object
    self.assertEqual(expected_stack[0][1], actual_stack[0][1])  # Filename
    self.assertEqual(expected_stack[0][2],
                     actual_stack[0][2] - 1)  # Line number
    self.assertEqual(expected_stack[0][3], actual_stack[0][3])  # Function name
    self.assertEqual(expected_stack[1:], actual_stack[1:])

  def testIsAnyTargetMethod(self):
    class MyModule:

      def f(self, a):
        pass

      def __call__(self):
        pass

    module = MyModule()
    self.assertTrue(tf_inspect.isanytargetmethod(module))
    f = module.f
    self.assertTrue(tf_inspect.isanytargetmethod(f))
    f = functools.partial(f, 1)
    self.assertTrue(tf_inspect.isanytargetmethod(f))
    f = test_decorator('tf_decorator1')(f)
    self.assertTrue(tf_inspect.isanytargetmethod(f))
    f = test_decorator('tf_decorator2')(f)
    self.assertTrue(tf_inspect.isanytargetmethod(f))

    class MyModule2:
      pass
    module = MyModule2()
    self.assertFalse(tf_inspect.isanytargetmethod(module))
    def f2(x):
      del x
    self.assertFalse(tf_inspect.isanytargetmethod(f2))
    f2 = functools.partial(f2, 1)
    self.assertFalse(tf_inspect.isanytargetmethod(f2))
    f2 = test_decorator('tf_decorator1')(f2)
    self.assertFalse(tf_inspect.isanytargetmethod(f2))
    f2 = test_decorator('tf_decorator2')(f2)
    self.assertFalse(tf_inspect.isanytargetmethod(f2))
    self.assertFalse(tf_inspect.isanytargetmethod(lambda: None))
    self.assertFalse(tf_inspect.isanytargetmethod(None))
    self.assertFalse(tf_inspect.isanytargetmethod(1))


class TfInspectGetCallArgsTest(test.TestCase):

  def testReturnsEmptyWhenUnboundFuncHasNoParameters(self):

    def empty():
      pass

    self.assertEqual({}, tf_inspect.getcallargs(empty))

  def testClashingParameterNames(self):

    def func(positional, func=1, func_and_positional=2, kwargs=3):
      return positional, func, func_and_positional, kwargs

    kwargs = {}
    self.assertEqual(
        tf_inspect.getcallargs(func, 0, **kwargs), {
            'positional': 0,
            'func': 1,
            'func_and_positional': 2,
            'kwargs': 3
        })
    kwargs = dict(func=4, func_and_positional=5, kwargs=6)
    self.assertEqual(
        tf_inspect.getcallargs(func, 0, **kwargs), {
            'positional': 0,
            'func': 4,
            'func_and_positional': 5,
            'kwargs': 6
        })

  def testUnboundFuncWithOneParamPositional(self):

    def func(a):
      return a

    self.assertEqual({'a': 5}, tf_inspect.getcallargs(func, 5))

  def testUnboundFuncWithTwoParamsPositional(self):

    def func(a, b):
      return (a, b)

    self.assertEqual({'a': 10, 'b': 20}, tf_inspect.getcallargs(func, 10, 20))

  def testUnboundFuncWithOneParamKeyword(self):

    def func(a):
      return a

    self.assertEqual({'a': 5}, tf_inspect.getcallargs(func, a=5))

  def testUnboundFuncWithTwoParamsKeyword(self):

    def func(a, b):
      return (a, b)

    self.assertEqual({'a': 6, 'b': 7}, tf_inspect.getcallargs(func, a=6, b=7))

  def testUnboundFuncWithOneParamDefault(self):

    def func(a=13):
      return a

    self.assertEqual({'a': 13}, tf_inspect.getcallargs(func))

  def testUnboundFuncWithOneParamDefaultOnePositional(self):

    def func(a=0):
      return a

    self.assertEqual({'a': 1}, tf_inspect.getcallargs(func, 1))

  def testUnboundFuncWithTwoParamsDefaultOnePositional(self):

    def func(a=1, b=2):
      return (a, b)

    self.assertEqual({'a': 5, 'b': 2}, tf_inspect.getcallargs(func, 5))

  def testUnboundFuncWithTwoParamsDefaultTwoPositional(self):

    def func(a=1, b=2):
      return (a, b)

    self.assertEqual({'a': 3, 'b': 4}, tf_inspect.getcallargs(func, 3, 4))

  def testUnboundFuncWithOneParamDefaultOneKeyword(self):

    def func(a=1):
      return a

    self.assertEqual({'a': 3}, tf_inspect.getcallargs(func, a=3))

  def testUnboundFuncWithTwoParamsDefaultOneKeywordFirst(self):

    def func(a=1, b=2):
      return (a, b)

    self.assertEqual({'a': 3, 'b': 2}, tf_inspect.getcallargs(func, a=3))

  def testUnboundFuncWithTwoParamsDefaultOneKeywordSecond(self):

    def func(a=1, b=2):
      return (a, b)

    self.assertEqual({'a': 1, 'b': 4}, tf_inspect.getcallargs(func, b=4))

  def testUnboundFuncWithTwoParamsDefaultTwoKeywords(self):

    def func(a=1, b=2):
      return (a, b)

    self.assertEqual({'a': 3, 'b': 4}, tf_inspect.getcallargs(func, a=3, b=4))

  def testBoundFuncWithOneParam(self):

    class Test(object):

      def bound(self):
        pass

    t = Test()
    self.assertEqual({'self': t}, tf_inspect.getcallargs(t.bound))

  def testBoundFuncWithManyParamsAndDefaults(self):

    class Test(object):

      def bound(self, a, b=2, c='Hello'):
        return (a, b, c)

    t = Test()
    self.assertEqual({
        'self': t,
        'a': 3,
        'b': 2,
        'c': 'Goodbye'
    }, tf_inspect.getcallargs(t.bound, 3, c='Goodbye'))

  def testClassMethod(self):

    class Test(object):

      @classmethod
      def test(cls, a, b=3, c='hello'):
        return (a, b, c)

    self.assertEqual({
        'cls': Test,
        'a': 5,
        'b': 3,
        'c': 'goodbye'
    }, tf_inspect.getcallargs(Test.test, 5, c='goodbye'))

  def testUsesOutermostDecoratorsArgSpec(self):

    def func():
      pass

    def wrapper(*args, **kwargs):
      return func(*args, **kwargs)

    decorated = tf_decorator.make_decorator(
        func,
        wrapper,
        decorator_argspec=tf_inspect.FullArgSpec(
            args=['a', 'b', 'c'],
            varargs=None,
            kwonlyargs={},
            defaults=(3, 'hello'),
            kwonlydefaults=None,
            varkw=None,
            annotations=None))

    self.assertEqual({
        'a': 4,
        'b': 3,
        'c': 'goodbye'
    }, tf_inspect.getcallargs(decorated, 4, c='goodbye'))


if __name__ == '__main__':
  test.main()
