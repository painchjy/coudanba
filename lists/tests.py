from django.test import TestCase

class HomePageTest(TestCase):


    def test_home_page_returns_correct_html(self):
        response = self.client.get('/')
        #html = response.content.decode('utf8')
        #print(repr(html))
        #self.assertIn('<title>To-Do lists</title>',html)
        #self.assertTrue(html.strip().endswith('</html>'))
        self.assertTemplateUsed(response, 'home.html')

