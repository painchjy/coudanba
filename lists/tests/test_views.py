from django.test import TestCase
from lists.models import Item, List, Ju
from django.utils.html import escape
from lists.forms import (
    DUPLICATE_ITEM_ERROR, EMPTY_ITEM_ERROR, NEED_TO_LOGIN_ERROR, ORDER_FORMAT_ERROR,
    ExistingListItemForm, ItemForm,
)
from unittest import skip
from django.contrib.auth import get_user_model
User = get_user_model()
import unittest
from unittest.mock import patch, Mock
from django.http import HttpRequest
from lists.views import new_list
from fixtures.ju import FIXTURE_JU_CONTENT
    
class MyListsTest(TestCase):

    def test_my_lists_url_renders_my_lists_template(self):
        User.objects.create(email='a@b.com')
        response = self.client.get('/lists/users/a@b.com/')
        self.assertTemplateUsed(response, 'my_lists.html')

    def test_passes_correct_owner_to_template(self):
        User.objects.create(email='wrong@owner.com')
        correct_user = User.objects.create(email='a@b.com')
        response = self.client.get('/lists/users/a@b.com/')
        self.assertEqual(response.context['owner'], correct_user)

class HomePageTest(TestCase):
    def test_home_page_uses_item_form_if_user_authenticated_with_active_ju(self):
        user = User.objects.create(email='a@b.com')
        self.client.force_login(user)
        active_ju = Ju.objects.create(content=FIXTURE_JU_CONTENT)
        response = self.client.get('/')
        self.assertIsInstance(response.context['form'], ItemForm)
        self.assertIsInstance(response.context['active_ju'], Ju)
        self.assertContains(response, escape(active_ju.address))
        self.assertContains(response, escape(active_ju.items[0]['desc']))

    
    def test_home_page_can_start_a_custome_bill_form_with_no_active_ju(self):
        response = self.client.get('/')
        self.assertIsInstance(response.context['form'], ItemForm)
        # ...
        self.assertFalse(response.context['form'].fields['text'].widget.attrs['readonly'])
    
    def test_home_page_cando_nothing_but_login_if_user_didnt_authenticated(self):
        # active_ju = Ju.objects.create(content=FIXTURE_JU_CONTENT)
        response = self.client.post('/',data={'text': 'A 1'})
        self.assertIsInstance(response.context['form'], ItemForm)
        self.assertContains(response, escape(NEED_TO_LOGIN_ERROR))

    def test_home_page_returns_correct_html(self):
        response = self.client.get('/')
        self.assertTemplateUsed(response, 'home.html')

    def test_only_saves_items_when_necessary(self):
        self.client.get('/')
        self.assertEqual(Item.objects.count(),0)

@patch('lists.views.Ju')
@patch('lists.views.NewListForm')
class NewListViewUnitTest(unittest.TestCase):
    def setUp(self):
        self.request = HttpRequest()
        self.request.POST['text'] = 'new list item'
        self.request.user = Mock()

    def test_passes_POST_data_to_NewListForm(self, mockNewListForm, mockJu):
        new_list(self.request)
        mockNewListForm.assert_called_once_with(data=self.request.POST)

    def test_saves_form_with_owner_if_form_valid(self, mockNewListForm, mockJu):
        mock_form = mockNewListForm.return_value
        mock_form.is_valid.return_value = True
        new_list(self.request)
        mock_form.save.assert_called_once_with(ju=mockJu.active_ju(), owner=self.request.user)

    @patch('lists.views.redirect')
    def test_redirects_to_form_returned_object_if_form_valid(
        self, mock_redirect, mockNewListForm, mockJu
    ):
        mock_form = mockNewListForm.return_value
        mock_form.is_valid.return_value = True

        response = new_list(self.request)

        self.assertEqual(response, mock_redirect.return_value)
        mock_redirect.assert_called_once_with(mock_form.save.return_value)
        
    @patch('lists.views.render')
    def test_renders_home_template_with_form_if_form_invalid(
        self, mock_render, mockNewListForm, mockJu
    ):
        mock_form = mockNewListForm.return_value
        mock_form.is_valid.return_value = False

        response = new_list(self.request)

        self.assertEqual(response, mock_render.return_value)
        mock_render.assert_called_once_with(
                self.request, 'home.html', {'form': mock_form, 'active_ju': mockJu.active_ju()}
        )

    def test_does_not_save_if_form_invalid(self, mockNewListForm, mockJu):
        mock_form = mockNewListForm.return_value
        mock_form.is_valid.return_value = False
        new_list(self.request)
        self.assertFalse(mock_form.save.called)



class NewListViewIntergratedTest(TestCase):
    def test_for_invalid_input_doesnt_save_but_show_errors(self):
        response = self.client.post('/lists/new', data={'text':''})
        self.assertEqual(List.objects.count(), 0)
        self.assertContains(response, escape(EMPTY_ITEM_ERROR))

    def test_list_owner_is_saved_if_user_is_authenticated(self):
        user = User.objects.create(email='a@b.com')
        self.client.force_login(user)
        active_ju = Ju.objects.create(content=FIXTURE_JU_CONTENT)
        self.client.post('/lists/new', data={'text': 'new item'})
        list_ = List.objects.first()
        self.assertEqual(list_.owner, user)


class ListViewTest(TestCase):
    def post_input(self,item_text):
        active_ju = Ju.objects.create(content=FIXTURE_JU_CONTENT)
        list_ = List.objects.create(owner=User(),ju=active_ju)
        return self.client.post(
            f'/lists/{list_.id}/',
            data={'text': item_text}
        )

    def test_display_item_form(self):
        active_ju = Ju.objects.create(content=FIXTURE_JU_CONTENT)
        list_ = List.objects.create(owner=User(),ju=active_ju)
        response = self.client.get(f'/lists/{list_.id}/')
        self.assertIsInstance(response.context['form'], ExistingListItemForm)
        self.assertContains(response, 'name="text"')

    def test_for_invalid_input_nothing_saved_to_db(self):
        self.post_input('')
        self.assertEqual(Item.objects.count(),0)

    def test_for_invalid_input_renders_list_template(self):
        response = self.post_input('')
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'list.html')

    def test_for_invalid_input_passes_form_to_template(self):
        response = self.post_input('')
        self.assertIsInstance(response.context['form'], ExistingListItemForm)

    def test_for_invalid_input_shows_error_on_page(self):
        response = self.post_input('')
        self.assertContains(response, escape(EMPTY_ITEM_ERROR))


    def test_passes_correct_list_to_template(self):
        other_list = List.objects.create(owner=User(),ju=Ju.objects.create())
        correct_list = List.objects.create(owner=User(),ju=Ju.objects.create())
        response = self.client.get('/lists/%d/' % (correct_list.id,))
        self.assertEqual(response.context['list'], correct_list)

    def test_use_list_template(self):
        list_ = List.objects.create(owner=User(),ju=Ju.objects.create())
        response  = self.client.get('/lists/%d/' % (list_.id,))
        self.assertTemplateUsed(response, 'list.html')

    def test_displays_only_items_for_that_list(self):
        correct_list = List.objects.create(owner=User(),ju=Ju.objects.create())
        Item.objects.create(text='itemey 1', list=correct_list)
        Item.objects.create(text='itemey 2', list=correct_list)
        other_list = List.objects.create(owner=User(),ju=Ju.objects.create())
        Item.objects.create(text='other list item 1', list=other_list)
        Item.objects.create(text='other list item 2', list=other_list)
        
        response = self.client.get('/lists/%d/' % (correct_list.id,))

        self.assertContains(response, 'itemey 1')
        self.assertContains(response, 'itemey 2')
        self.assertNotContains(response, 'other list item 1')
        self.assertNotContains(response, 'other list item 2')

    def test_can_save_a_POST_request_to_an_existing_list(self):
        other_list = List.objects.create(owner=User(),ju=Ju.objects.create())
        correct_list = List.objects.create(owner=User(),ju=Ju.objects.create())

        self.client.post(
            f'/lists/{correct_list.id}/',
            data={'text': 'A new item for an existing list'}
        )

        self.assertEqual(Item.objects.count(), 1)
        new_item = Item.objects.first()
        self.assertEqual(new_item.text, 'A new item for an existing list')
        self.assertEqual(new_item.list, correct_list)


    def test_POST_redirects_to_list_view(self):
        other_list = List.objects.create(owner=User(),ju=Ju.objects.create())
        correct_list = List.objects.create(owner=User(),ju=Ju.objects.create())

        response = self.client.post(
            f'/lists/{correct_list.id}/',
            data={'text': 'A new item for an existing list'}
        )

        self.assertRedirects(response, f'/lists/{correct_list.id}/')

    def test_for_invalid_order_format_shows_error_on_page(self):
        response = self.post_input('A')
        self.assertContains(response, escape(ORDER_FORMAT_ERROR))

    def test_for_valid_order_format_shows_correct_order_and_prices_on_page(self):
        response = self.post_input('A 1')
        print('------++++++++++___________')
        print(escape(response.context))

    def test_duplicate_item_validation_errors_end_up_on_list_page(self):
        list_ = List.objects.create(owner=User(),ju=Ju.objects.create())
        item1 = Item.objects.create(list=list_, text='textey')
        response = self.client.post(
            f'/lists/{list_.id}/',
            data={'text': 'textey'}
        )

        expected_error = escape( DUPLICATE_ITEM_ERROR )
        self.assertContains(response, expected_error)
        self.assertTemplateUsed(response, 'list.html')
        self.assertEqual(Item.objects.all().count(),1)

