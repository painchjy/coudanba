from .base import FunctionalTest
from unittest import skip
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from django.utils.html import escape
import time,re


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

    def test_one_item_price_update_all_lists_cost_updated_too(self):
        email = 'edith@example.com'
        self.load_fixture_user(email)
        # Edith is a logged-in user
        session_key = self.create_pre_authenticated_session(email)
        active_ju = self.load_fixture_ju()

        # She goes to the home page and starts a list
        self.browser.get(self.live_server_url)
        self.wait_to_be_logged_in(email)

        # She  orders one product A
        inputbox = self.get_item_input_box()
        inputbox.clear()
        inputbox.send_keys('A 1')

        # When she hits enter, the page updates, and now the page lists
        # Product A and  1 QTY shows in the list table
        inputbox.send_keys(Keys.ENTER)
        self.wait_for_row_order_in_list_table('1: A', 1, active_ju.items['A']['price'],active_ju.items['A']['price'])


        # There is still a text box inviting her to add another item. She
        # enters "b 2"
        inputbox = self.get_item_input_box()
        inputbox.send_keys('b 1.5')
        inputbox.send_keys(Keys.ENTER)

        # The page updates again, and now shows both items on her list
        self.wait_for_row_order_in_list_table('2: b', 1.5,active_ju.items['B']['price'], active_ju.items['B']['price']*1.5)
        self.wait_for_row_order_in_list_table('1: A', 1, active_ju.items['A']['price'],active_ju.items['A']['price'])

        # 把蓝莓价格改85后，查询原来的list_item价格也要变更
        active_ju.content = re.sub(r':45',':85',active_ju.content)
        print('-------------ju.content{}'.format(active_ju.content))
        active_ju.parse_content()
        active_ju.save()

        # 重新刷新页面，查看价格是否变更了
        self.browser.get(self.browser.current_url)
        self.wait_for_row_order_in_list_table('2: b', 1.5,85, 85*1.5)
        self.wait_for_row_order_in_list_table('1: A', 1, 31,31)

        




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

        # 先卖苹果和桔子试试看吧
        





