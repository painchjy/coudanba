from django.core import mail
from selenium.webdriver.common.keys import Keys
import os
import poplib
import re
import time

from .base import FunctionalTest

# TEST_EMAIL = '13916341082@163.com'
SUBJECT = 'Login URL from www.coudanba.cn'

class LoginTest(FunctionalTest):

    def wait_for_email(self, test_email, subject):
        if not self.staging_server:
            email = mail.outbox[0]
            self.assertIn(test_email, email.to)
            self.assertEqual(email.subject, subject)
            return email.body
        email_id = None
        start = time.time()
        inbox = poplib.POP3_SSL('pop.qq.com')
        try:
            inbox.user(test_email)
            inbox.pass_(os.environ['EMAIL_PASSWORD'])
            while time.time() - start < 60:
                count, _ = inbox.stat()
                for i in reversed(range(max(1,count - 10), count +1 )):
                    print('getting msg',i)
                    _, lines, __ = inbox.retr(i)
                    lines = [l.decode('utf8') for l in lines]
                    print(lines)
                    if subject in lines:
                        print('----found subject-----')
                        email_id = i
                        body = '\n'.join(lines)
                        return body
            time.sleep(5)
        finally:
            if email_id:
                inbox.dele(email_id)
            inbox.quit()


    def test_can_get_email_link_to_log_in(self):
        # Edith goes to the awsome superlists site
        # and notices a "log in" section in the navbar for the first time
        # It's telling her to enter her email address, so she does so
        if self.staging_server:
            test_email = '13916341082@qq.com'
        else:
            test_email = 'edith@example.com'

        self.load_fixture_user( test_email)
        self.browser.get(self.live_server_url)
        self.browser.find_element_by_name('email').send_keys(test_email)
        self.browser.find_element_by_name('email').send_keys(Keys.ENTER)

        # A message appears telling her an email has been sent
        self.wait_for(lambda: self.assertIn(
            '登录链接已发送，请检查你的邮箱',
            self.browser.find_element_by_tag_name('body').text
        ))

        # She checks her email and finds a message
        body = self.wait_for_email(test_email, SUBJECT)

        # It has a url link in it
        self.assertIn('请使用以下链接登录凑单吧：', body)
        url_search = re.search(r'http://.+/.+$', body)
        if not url_search:
            self.fail(f'Could not find url in email body:\n{body}')
        url = url_search.group(0)
        self.assertIn(self.live_server_url, url)

        # she clicks it
        self.browser.get(url)

        # she is logged in!
        self.wait_to_be_logged_in(email=test_email)

        # Now she logs out
        self.browser.find_element_by_link_text('注销').click()

        # She is logged out
        self.wait_to_be_logged_out(email=test_email)


