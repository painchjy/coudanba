from .base import FunctionalTest
from unittest import skip
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
import time
from jus.models import Ju

class NewVisitorTest(FunctionalTest):
    def test_new_user_can_see_error_with_no_active_ju(self):
        # edith has heard about a 凑单吧 site online. she goes
        # to check out its home page
        self.browser.get(self.live_server_url)
        # She notices the page title and header mention 凑单吧
        self.assertIn('凑单吧',self.browser.title)
        
        header_text = self.browser.find_element_by_tag_name('h4').text  
        self.assertIn('请扫码关注微信企业号或使用企业微信登录', header_text)

        
    @skip
    def test_new_user_can_see_active_ju_but_can_not_new_orders(self):
        # edith has heard about a 凑单吧 site online. she goes
        # to check out its home page
        self.load_fixture_ju()
        self.browser.get(self.live_server_url)
        # She notices the page title and header mention 凑单吧
        self.assertIn('凑单吧',self.browser.title)
        self.browser.find_element_by_link_text('看看别人在凑什么').click()
        time.sleep(2)
        header_text = self.browser.find_element_by_tag_name('h3').text  
        self.assertIn('活动说明', header_text)
        

        self.assertIn('截止时间', header_text)
        active_ju = Ju.active_ju()
        self.assertIn(active_ju.address, header_text)

        # There are some ju items list under the header
        items = active_ju.items
        for k,v in items.items():
            self.wait_for_row_in_ju_table(v['desc'])

        self.get_item_input_box().send_keys('A 1')
        self.get_item_input_box().send_keys(Keys.ENTER)
        # The home page refreshes, and there is an error message saying
        # that you have to login first
        self.wait_for(lambda: self.assertEqual(
            self.get_error_element().text,
            "别着急，先登录再凑单！"
        ))
