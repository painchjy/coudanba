from .base import FunctionalTest
from selenium.webdriver.common.keys import Keys
from unittest import skip
from lists.forms import DUPLICATE_ITEM_ERROR
from jus.models import Ju

class OrderValidation(FunctionalTest):
    def test_order_unit(self):
        email = 'edith@example.com'
        self.load_fixture_user(email)
        # Edith is a logged-in user
        # 定义单位为0.1的产品,用来测试精度，浮点数无法精确存储1/5,1/10
        # 可能导致判断1不是0.1的整数倍
        session_key = self.create_pre_authenticated_session(email)
        active_ju = self.load_fixture_ju()
        item_unit = {"unit":0.1}
        active_ju.items["A"].update(item_unit)
        active_ju.save()
        active_ju.db_triggers()

        # She goes to the home page and starts a list
        self.browser.get(self.live_server_url)
        self.wait_to_be_logged_in(email)


        # She is invited to make her first order
        inputbox = self.get_item_input_box()

        # She  orders one product A 
        inputbox = self.get_item_input_box()
        inputbox.clear()
        inputbox.send_keys('A 1')
        
        # When she hits enter, the page updates, and now the page lists
        # Product A and  1 QTY shows in the list table
        inputbox.send_keys(Keys.ENTER)
        self.wait_for_row_in_orders_table({'A': '1'}, active_ju, email, 'N/A')

        # She  orders one product A by 0.11 should be error
        inputbox = self.get_item_input_box()
        inputbox.clear()
        inputbox.send_keys('A 0.11')
        
        # When she hits enter, the page updates, and now the page lists
        # Product A and  1 QTY shows in the list table
        inputbox.send_keys(Keys.ENTER)
        self.wait_for(lambda: self.assertIn(
            "下单数量必须为0.10的倍数",
            self.get_error_element().text,
        ))
        
        # edith觉得输入空格太麻烦，直接输入编号和份数，发现也能成功 
        inputbox = self.get_item_input_box()
        inputbox.clear()
        inputbox.send_keys('A2')
        inputbox.send_keys(Keys.ENTER)
        self.wait_for_row_in_orders_table({'A': '2'}, active_ju, email, 'N/A')

        # edith想给活动发起人留言，输入编号和份数后面增加了留言，
        # 发现留言出现在自己的订单上。
        inputbox = self.get_item_input_box()
        inputbox.clear()
        inputbox.send_keys('A1周四下午提货')
        inputbox.send_keys(Keys.ENTER)
        self.wait_for_row_in_orders_table({'A': '1'}, active_ju, email, 'N/A', memo='周四下午提货')

        # edith输入编号B和份数后面增加了留言，
        # 发现留言更新了，原来的留言被覆盖了。
        inputbox = self.get_item_input_box()
        inputbox.clear()
        inputbox.send_keys('B1周四下午提货')
        inputbox.send_keys(Keys.ENTER)
        self.wait_for_row_in_orders_table({'B': '1'}, active_ju, email, 'N/A', memo='周四下午提货')

