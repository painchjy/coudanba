from django.test import TestCase

class HomePageTest(TestCase):


    def test_home_page_returns_correct_html(self):
        response = self.client.get('/')
        #html = response.content.decode('utf8')
        #print(repr(html))
        #self.assertIn('<title>To-Do lists</title>',html)
        #self.assertTrue(html.strip().endswith('</html>'))
        self.assertTemplateUsed(response, 'home.html')

    def test_can_save_a_POST_request(self):
        response = self.client.post('/', data={'item_text': 'A new list item'})
        self.assertIn('A new list item', response.content.decode())
        self.assertTemplateUsed(response, 'home.html')

