from django.test import TestCase
from django.conf import settings

from core.forms import LoginForm, RegisterForm
from core.models import ExtendedUser as User
from core.tests.util import checkAccessPermissions, PermissionLevel

##################################################################################
# Test cases for core
# @since 15 AUG 2019
##################################################################################

# Tests whether front-end pages can be accessed
class FrontEndTest(TestCase):
    fixtures = ['test_users.json']

    # Tests if the homepage can be accessed
    def test_homepage(self):
        checkAccessPermissions(self, '/', 'get', PermissionLevel.LEVEL_PUBLIC)

    # Tests if the login page can be accessed
    def test_login(self):
        checkAccessPermissions(self, settings.LOGIN_URL, 'get', PermissionLevel.LEVEL_PUBLIC)

    # Tests if the logout-success page can be accessed
    def test_logout_success(self):
        checkAccessPermissions(self, settings.LOGOUT_REDIRECT_URL, 'get', PermissionLevel.LEVEL_PUBLIC)
    
    # Tests if the logout-success page can be accessed if logged in
    def test_logout_success_when_logged_in(self):
        checkAccessPermissions(self, settings.LOGOUT_REDIRECT_URL, 'get', PermissionLevel.LEVEL_USER, redirectUrl=settings.LOGOUT_REDIRECT_URL)

    # Tests if the account page can be accessed
    def test_account(self):
        checkAccessPermissions(self, '/account', 'get', PermissionLevel.LEVEL_USER)

    # Tests if the logout page can be accessed if not logged in
    def test_logout_redirect(self):
        checkAccessPermissions(self, settings.LOGOUT_URL, 'get', PermissionLevel.LEVEL_PUBLIC, redirectUrl=settings.LOGOUT_REDIRECT_URL)

    # Tests if the register-page can be accessed
    def test_register(self):
        checkAccessPermissions(self, '/register', 'get', PermissionLevel.LEVEL_PUBLIC)

    # Tests if the register-success page can be accessed
    def test_register_success(self):
        checkAccessPermissions(self, '/register/success', 'get', PermissionLevel.LEVEL_PUBLIC)


# Tests the login form
class LoginFormTest(TestCase):
    def setUp(self):
        # Called each time before a testcase runs
        # Set up data for each test.
        self.user = User.objects.create_user(username="its-a-me", password="mario")
        User.save(self.user)

    # Test if a login is allowed if the username-password pair are correct
    def test_form_correct(self):
        form_data = {
            'username': 'its-a-me',
            'password': 'mario',        
        }
        form = LoginForm(data=form_data)
        # Data that was entered is correct
        self.assertTrue(form.is_valid())
    
    # Test if a login is disallowed if the username-password pair are incorrect
    def test_form_incorrect(self):
        form_data = {
            'username': 'its-a-me',
            'password': 'luigi',        
        }
        form = LoginForm(data=form_data)
        
        # Data that was entered is incorrect
        self.assertFalse(form.is_valid())

        # Ensure that only one (general) error was given
        self.assertEqual(len(form.errors.as_data()), 1)
        self.assertEqual(len(form.non_field_errors().as_data()), 1)
        self.assertEqual(form.non_field_errors().as_data()[0].code, 'ERROR_INVALID_LOGIN')
        
    # Test if a login is disallowed if the username is missing
    def test_form_username_missing(self):
        form_data = {
            'password': 'wario',        
        }
        form = LoginForm(data=form_data)
        
        # Data that was entered is incorrect
        self.assertFalse(form.is_valid())
        
        # Ensure that only one error was given
        self.assertTrue(form.has_error('username'))
        self.assertEqual(len(form.errors.as_data()), 1)


# Tests the register form
class RegisterFormTest(TestCase):
    def setUp(self):
        # Called each time before a testcase runs
        # Set up data for each test.
        self.user = User.objects.create_user(username="schaduwbestuur", password="bestaatniet", email='rva@example.com')
        User.save(self.user)

    # Test if the user can register if everything is correct
    def test_form_correct(self):
        form_data = {
            'username': 'schaduwkandi',
            'password1': 'bestaatookniet',
            'password2': 'bestaatookniet',
            'email': 'kandi@example.com', 
            'nickname': 'wijbestaanniet',
        }
        form = RegisterForm(data=form_data)

        # Data that was entered is correct
        self.assertTrue(form.is_valid())

        # Ensure the correct object is returned (but not saved)
        user = form.save(commit=False)
        self.assertIsNotNone(user)
        self.assertEquals(user.email, 'kandi@example.com')
        self.assertTrue(user.check_password('bestaatookniet'))
        self.assertEqual(user.first_name, 'wijbestaanniet')

        user = User.objects.filter(username='schaduwkandi').first()
        self.assertIsNone(user)

        # Ensure the correct data is saved
        form.save(commit=True)  
        user = User.objects.filter(username='schaduwkandi').first()
        self.assertIsNotNone(user)
        self.assertEquals(user.email, 'kandi@example.com')
        self.assertTrue(user.check_password('bestaatookniet'))
        self.assertEqual(user.first_name, 'wijbestaanniet')

    # Test if a registering fails if required fields are missing
    def test_form_fields_missing(self):
        form_data = {
            'nickname': 'empty',       
        }
        form = RegisterForm(data=form_data)
        
        # Data that was entered is incorrect
        self.assertFalse(form.is_valid())
        
        # Ensure that only one error was given per missing field
        self.assertTrue(form.has_error('username'))
        self.assertEqual(len(form.errors.as_data()['username']), 1)
        self.assertTrue(form.has_error('password1'))
        self.assertEqual(len(form.errors.as_data()['password1']), 1)
        self.assertTrue(form.has_error('password2'))
        self.assertEqual(len(form.errors.as_data()['password2']), 1)
        self.assertTrue(form.has_error('email'))
        self.assertEqual(len(form.errors.as_data()['email']), 1)
        self.assertEqual(len(form.errors.as_data()), 4)

    # Test if a registering fails if the two passwords do not match
    def test_form_nonmatching_password(self):
        form_data = {
            'username': 'schaduwkandi',
            'password1': 'bestaatookniet',
            'password2': 'nomatch',
            'email': 'kandi@example.com', 
            'nickname': 'wijbestaanniet',
        }
        form = RegisterForm(data=form_data)
        
        # Data that was entered is incorrect
        self.assertFalse(form.is_valid())
        
        # Ensure that only one error was given
        self.assertTrue(form.has_error('password2'))
        self.assertEqual(len(form.errors.as_data()['password2']), 1)
   
    # Test if a registering fails if username or email was already chosen by another user
    def test_form_duplicate_field(self):
        form_data = {
            'username': 'schaduwbestuur',
            'password1': 'secret',
            'password2': 'secret',
            'email': 'rva@example.com', 
            'nickname': 'wijbestaanniet',
        }
        form = RegisterForm(data=form_data)
        
        # Data that was entered is incorrect
        self.assertFalse(form.is_valid())
        
        # Ensure that only one error was given
        self.assertTrue(form.has_error('username'))
        self.assertEqual(len(form.errors.as_data()['username']), 1)
        self.assertTrue(form.has_error('email'))
        self.assertEqual(len(form.errors.as_data()['email']), 1)


# Tests the registerForm view
class RegisterFormViewTest(TestCase):
    fixtures = ['test_users.json']

    # Tests if redirected when form data was entered correctly
    def test_success_redirect(self):
        form_data = {
            'username': 'username',
            'password1': 'thisactuallyneedstobeagoodpassword',
            'password2': 'thisactuallyneedstobeagoodpassword',
            'email': 'email@example.com',
        }
        checkAccessPermissions(self, '/register', 'post', PermissionLevel.LEVEL_PUBLIC,
                redirectUrl='/register/success', data=form_data)
        
        user = User.objects.filter(username='username').first()
        self.assertIsNotNone(user)
        self.assertEquals(user.email, 'email@example.com')
        self.assertTrue(user.check_password('thisactuallyneedstobeagoodpassword'))
        self.assertEqual(user.first_name, '')

    # Tests if not redirected when form data was entered incorrectly
    def test_fail_form_enter(self):
        form_data = {
            'username': 'username',
            'password1': 'password', # Password too easy so should fail
            'password2': 'password',
            'email': 'email@example.com',
        }
        checkAccessPermissions(self, '/register', 'post', PermissionLevel.LEVEL_PUBLIC, data=form_data)

        user = User.objects.filter(username='username').first()
        self.assertIsNone(user)
