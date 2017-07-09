from .base import FunctionalTest
from unittest import skip
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from django.utils.html import escape
import time


class JuLifeCycleTest(FunctionalTest):

    def test_ju_status_active_deactive(self):
        # edith发现聚活动的状态从active改变成其他状态后，就不能再下单了
        email = 'edith@example.com'
        self.load_fixture_user(email)
        # Edith is a logged-in user
        session_key = self.create_pre_authenticated_session(email)
        active_ju = self.load_fixture_ju()
        # 聚活动状态被修改后
        active_ju.status = 'close'
        active_ju.save()

        # She goes to the home page and starts a list
        self.browser.get(self.live_server_url + '/lists/order/{}/'.format(active_ju.id))
        self.wait_to_be_logged_in(email)


        # She is invited to make her first order
        inputbox = self.get_item_input_box()
        self.assertTrue(inputbox.get_attribute('readonly'))

    def test_ju_creation(self):
        # edith 通过高人指点，搞到了黑后台的url
        # 发现可以自己创建一个新的活动
        email = 'edith@example.com'
        self.load_fixture_user(email)
        # Edith is a logged-in user
        session_key = self.create_pre_authenticated_session(email)

        self.browser.get(self.live_server_url + '/jus/new/')
        self.wait_to_be_logged_in(email)
        
        inputbox = self.get_item_input_box_by_id('id_content')
        self.assertIn(
            '#@!@#$$%%#',
            inputbox.get_attribute('placeholder')
        )

        self.fail('Finish the test!')
        # 搞定一堆输入框，选择活动地点和群组范围

        # 先买苹果和桔子试试看吧
        





