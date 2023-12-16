# -*- coding: utf-8 -*-
"""
Created on Fri Nov 17 08:03:28 2023

@author: Panda Jiang
"""

import unittest

from hello import sayhello



# 测试用例继承 unittest.TestCase 类，在这个类中创建的以 test_ 开头的方法将会被视为测试方法。
# 内容为空的两个方法很特殊，它们是测试固件，用来执行一些特殊操作。
# 比如 setUp() 方法会在每个测试方法执行前被调用，而 tearDown() 方法则会在每一个测试方法执行后被调用（注意这两个方法名称的大小写）。
# 如果把执行测试方法比作战斗，那么准备弹药、规划战术的工作就要在 setUp() 方法里完成，而打扫战场则要在 tearDown() 方法里完成。
# 每一个测试方法（名称以 test_ 开头的方法）对应一个要测试的函数 / 功能 / 使用场景。
# 在上面我们创建了两个测试方法，test_sayhello() 方法测试 sayhello() 函数，test_sayhello_to_somebody() 方法测试传入参数时的 sayhello() 函数。
# 在测试方法里，我们使用断言方法来判断程序功能是否正常。
#   以第一个测试方法为例，我们先把 sayhello() 函数调用的返回值保存为 rv 变量（return value）
#   然后使用 self.assertEqual(rv, 'Hello!') 来判断返回值内容是否符合预期。
#   如果断言方法出错，就表示该测试方法未通过。



class SayHelloTestCase(unittest.TestCase):  # 测试用例

    def setUp(self):  # 测试固件
        pass

    def tearDown(self):  # 测试固件
        pass

    def test_sayhello(self):  # 第 1 个测试
        rv = sayhello()
        self.assertEqual(rv, 'Hello!')

    def test_sayhello_to_somebody(self):  # 第 2 个测试
        rv = sayhello(to='Grey')
        self.assertEqual(rv, 'Hello, Grey!')


if __name__ == '__main__':
    unittest.main()