from .base import FunctionalTest
from unittest import skip
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
import time
from lists.models import Ju

class NewVisitorTest(FunctionalTest):
    def test_new_user_can_see_error_with_no_active_ju(self):
        # edith has heard about a 聚一聚 site online. she goes
        # to check out its home page
        self.browser.get(self.live_server_url)
        # She notices the page title and header mention 上丰路聚一聚
        self.assertIn('聚一聚',self.browser.title)
        
        header_text = self.browser.find_element_by_tag_name('h2').text  
        self.assertIn('活动还没开始呢！不过你可以先玩一玩记账。', header_text)

        
    def test_new_user_can_see_active_ju_but_can_not_new_orders(self):
        # edith has heard about a 聚一聚 site online. she goes
        # to check out its home page
        self.load_fixture_ju()
        self.browser.get(self.live_server_url)
        # She notices the page title and header mention 上丰路聚一聚
        self.assertIn('聚一聚',self.browser.title)
        
        time.sleep(2)
        header_text = self.browser.find_element_by_tag_name('h2').text  
        self.assertIn('提货地点', header_text)
        

        self.assertIn('截止时间', header_text)
        active_ju = Ju.active_ju()
        self.assertIn(active_ju.address, header_text)
        self.assertIn(active_ju.stop_date, header_text)

        # There are some ju items list under the header
        items = active_ju.items
        for k,v in items.items():
            self.wait_for_row_in_ju_table(v['desc'])

        self.get_item_input_box().send_keys('A:1')
        self.get_item_input_box().send_keys(Keys.ENTER)
        # The home page refreshes, and there is an error message saying
        # that you have to login first
        self.wait_for(lambda: self.assertEqual(
            self.get_error_element().text,
            "别着急，先登录再下单！"
        ))
