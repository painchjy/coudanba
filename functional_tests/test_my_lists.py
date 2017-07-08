from .base import FunctionalTest
from django.contrib.auth import BACKEND_SESSION_KEY, SESSION_KEY, get_user_model
from django.contrib.sessions.backends.db import SessionStore
import time
from unittest import skip
User = get_user_model()

class MyListsTest(FunctionalTest):

    @skip
    def test_logged_in_users_lists_are_saved_as_my_lists(self):
        email = 'edith@example.com'
        self.load_fixture_user(email=email)
        self.browser.get(self.live_server_url)
        self.wait_to_be_logged_out(email)

        # Edith is a logged-in user
        self.create_pre_authenticated_session(email)

        # She goes to the home page and starts a list
        self.browser.get(self.live_server_url)
        self.wait_to_be_logged_in(email)
        self.add_list_item('Reticulate splines')
        self.add_list_item('Immanentize eschaton')
        first_list_url = self.browser.current_url

        # She notices a "My lists" link, for the first time.
        self.browser.find_element_by_link_text('我的凑单').click()

        # She sees that her list is in there, named according to its
        # first list item
        self.wait_for(
            lambda: self.browser.find_element_by_partial_link_text('Reticulate splines')
        )
        self.browser.find_element_by_partial_link_text('Reticulate splines').click()
        self.wait_for(
            lambda: self.assertEqual(self.browser.current_url, first_list_url)
        )

        # She decides to start anther list ,just to see
        self.browser.get(self.live_server_url)
        self.add_list_item('Click cows')
        second_list_url = self.browser.current_url

        # Under "My lists", her new list appears
        self.browser.find_element_by_link_text('我的凑单').click()
        self.wait_for(
            lambda: self.browser.find_element_by_partial_link_text('Click cows')
        )
        self.browser.find_element_by_partial_link_text('Click cows').click()
        self.wait_for(
            lambda: self.assertEqual(self.browser.current_url, second_list_url)
        )

        # She logs out. The "My lists" option disappears
        self.browser.find_element_by_link_text('注销').click()
        self.wait_to_be_logged_out(email)
        self.wait_for(lambda: self.assertEqual(
            self.browser.find_elements_by_link_text('我的凑单'),
            []
        ))


        
    def test_users_cannot_open_other_users_list_by_url(self):
        email = 'edith@example.com'
        self.load_fixture_user(email=email)
        self.browser.get(self.live_server_url)
        self.wait_to_be_logged_out(email)

        # Edith is a logged-in user
        self.create_pre_authenticated_session(email)

        # She goes to the home page and starts a list
        self.browser.get(self.live_server_url)
        self.wait_to_be_logged_in(email)
        self.add_list_item('Reticulate splines')
        self.add_list_item('Immanentize eschaton')
        first_list_url = self.browser.current_url

    
        self.browser.find_element_by_link_text('注销').click()
        self.wait_to_be_logged_out(email)
        
        self.browser.get(first_list_url)
        self.assertNotEqual(self.browser.current_url, first_list_url)
        self.assertEqual(self.browser.current_url, self.live_server_url + '/')

        email = 'blink@example.com'
        self.load_fixture_user(email=email)
        self.create_pre_authenticated_session(email)
        self.browser.get(self.live_server_url)
        self.wait_to_be_logged_in(email)
        self.browser.get(first_list_url)
        self.assertNotEqual(self.browser.current_url, first_list_url)
        self.assertEqual(self.browser.current_url, self.live_server_url + '/')


    def test_a_list_without_owner_can_be_open_by_anyone_by_url(self):
        email = 'edith@example.com'
        self.load_fixture_user(email=email)
        self.browser.get(self.live_server_url)
        self.wait_to_be_logged_out(email)
        self.add_list_item('Reticulate splines')
        self.add_list_item('Immanentize eschaton')
        first_list_url = self.browser.current_url

        # Edith is a logged-in user
        self.create_pre_authenticated_session(email)

        # She goes to the home page and starts a list
        self.browser.get(self.live_server_url)
        self.wait_to_be_logged_in(email)

        self.browser.get(first_list_url)
        self.assertEqual(self.browser.current_url, first_list_url)
    
        self.browser.find_element_by_link_text('注销').click()
        self.wait_to_be_logged_out(email)
        self.browser.get(self.live_server_url)
        self.wait_to_be_logged_out(email)
        self.browser.get(first_list_url)
        self.assertEqual(self.browser.current_url, first_list_url)


    
    
