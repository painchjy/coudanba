from .base import FunctionalTest
from unittest import skip
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from django.utils.html import escape
import time
from django.conf import settings

class NewVisitorTest(FunctionalTest):
    def test_can_start_a_bill_for_one_user_without_ju(self):
        # Edith just known a cool site call ju1ju app. She goes
        # to check its homepage, try to find something interesting
        ## self.browser.get('http://localhost:8000') ## 要使用测试库，要通过live_server_url访问,测试环境使用8081端口

        # She goes to the home page and was invited to start a bill
        self.browser.get(self.live_server_url)


        # She is invited to make her first order
        inputbox = self.get_item_input_box()
        self.assertEqual(
            '怎么填都行',
            inputbox.get_attribute('placeholder'),
            "Attribute placeholder for the inputbox not exists or not set the correct value"
        )
        
        # She  orders one product A 
        inputbox.send_keys('车厘子 1.5 129.9')
        
        # When she hits enter, the page updates, and now the page lists
        # Product A and  1 QTY shows in the list table
        inputbox.send_keys(Keys.ENTER)
        self.wait_for_row_order_in_list_table('1: 车厘子', 1.5,129.9, 129.9*1.5)

        
        # There is still a text box inviting her to add another item. She
        # enters "T-shirt 2 19" 
        inputbox = self.get_item_input_box()
        inputbox.send_keys('T-shirt 2  39')
        inputbox.send_keys(Keys.ENTER)
        
        # The page updates again, and now shows both items on her list
        self.wait_for_row_order_in_list_table('1: 车厘子', 1.5,129.9, 129.9*1.5)
        self.wait_for_row_order_in_list_table('2: T-shirt', 2,39, 39*2)
        
        # Satisfied, she goes back to sleep
    
    def test_can_start_a_new_order_for_one_user_with_ju(self):
        # Edith login to ju1ju app. She goes
        # to check its homepage, try to make orders
        ## self.browser.get('http://localhost:8000') ## 要使用测试库，要通过live_server_url访问,测试环境使用8081端口
        email = 'edith@example.com'
        # Edith is a logged-in user
        session_key = self.create_pre_authenticated_session(email)
        active_ju = self.load_fixture_ju()

        # She goes to the home page and starts a list
        self.browser.get(self.live_server_url)
        self.wait_to_be_logged_in(email)


        # She is invited to make her first order
        inputbox = self.get_item_input_box()
        self.assertEqual(
            '输入：代号 数量；示例：A 1.5',
            inputbox.get_attribute('placeholder'),
            "Attribute placeholder for the inputbox not exists or not set the correct value"
        )
        
        # She try to add and unexisted item "c 2" 
        inputbox = self.get_item_input_box()
        inputbox.send_keys('c 1.5')
        inputbox.send_keys(Keys.ENTER)

        self.wait_for(lambda: self.assertIn(
            "什么代号啊亲！",
            self.get_error_element().text,
        ))

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
        
        # There is still a text box inviting her to add another item. She
        # try to add and unexisted item "c 2" 
        inputbox = self.get_item_input_box()
        inputbox.send_keys('c 1.5')
        inputbox.send_keys(Keys.ENTER)

        self.wait_for(lambda: self.assertIn(
            "什么代号啊亲！",
            self.get_error_element().text,
        ))
        # Satisfied, she goes back to sleep


        # Edith wonders whether the site will remember her list. Then she sees
        # that the site has generated a unique URL for her -- there is some
        # explanatory text to that effect.
        #self.browser.quit()
        #self.browser = webdriver.Firefox()
        self.browser.find_element_by_link_text('注销').click()
        self.wait_to_be_logged_out(email)
        #email = 'edith@example.com'
        # Edith is a logged-in user
        self.create_pre_authenticated_session(email)
        # She goes to the home page and see the order she make yestoday
        self.browser.get(self.live_server_url)
        self.wait_to_be_logged_in(email)


        # The page shows what she saw yestoday
        self.wait_for_row_order_in_list_table('2: b', 1.5,active_ju.items['B']['price'], active_ju.items['B']['price']*1.5)
        self.wait_for_row_order_in_list_table('1: A', 1, active_ju.items['A']['price'],active_ju.items['A']['price'])

        # There is still a text box inviting her to add another item. She
        # want to change item b to "B 3" 
        inputbox = self.get_item_input_box()
        inputbox.clear()
        inputbox.send_keys('B 3')
        inputbox.send_keys(Keys.ENTER)
        
        # The page updates again, and now shows both items on her list
        self.wait_for_row_order_in_list_table('2: B', 3,active_ju.items['B']['price'], active_ju.items['B']['price']*3)
        self.wait_for_row_order_not_in_list_table('2: b', 1.5,active_ju.items['B']['price'], active_ju.items['B']['price']*1.5)
        # Satisfied, she goes back to sleep

    def test_multiple_users_can_start_lists_at_different_urls(self):
        # Edith wonders whether the site will remember her list. Then she sees
        # that the site has generated a unique URL for her -- there is some
        # explanatory text to that effect.
        self.browser.get(self.live_server_url)
        inputbox = self.get_item_input_box()
        inputbox.send_keys('Buy peacock feathers')
        inputbox.send_keys(Keys.ENTER)
        self.wait_for_row_in_list_table('1: Buy peacock feathers')
        
        # She notices that her list has a unique URL
        edith_list_url = self.browser.current_url
        self.assertRegex(edith_list_url, '/lists/.+')

        # Now a new user, Francis, comes along to the site.

        ## We use a new browser session to make sure that no information
        ## of Edith's is coming through from cookies etc
        self.browser.quit()
        self.browser = webdriver.Firefox()

        # Francis visits the home page.  There is no sign of Edith's
        # list
        self.browser.get(self.live_server_url)
        page_text = self.browser.find_element_by_tag_name('body').text
        self.assertNotIn('Buy peacock feathers', page_text)
        self.assertNotIn('make a fly', page_text)

        # Francis starts a new list by entering a new item. He
        # is less interesting than Edith...
        inputbox = self.get_item_input_box()
        inputbox.send_keys('Buy milk')
        inputbox.send_keys(Keys.ENTER)
        self.wait_for_row_in_list_table('1: Buy milk')

        # Francis gets his own unique URL
        francis_list_url = self.browser.current_url
        self.assertRegex(francis_list_url, '/lists/.+')
        self.assertNotEqual(francis_list_url, edith_list_url)
        # Again, there is no trace of Edith's list
        page_text = self.browser.find_element_by_tag_name('body').text
        self.assertNotIn('Buy peacock feathers', page_text)
        self.assertIn('Buy milk', page_text)

        # Satisfied, they both go back to sleep

