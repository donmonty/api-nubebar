from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse

from rest_framework.test import APIClient
from rest_framework import status


CREATE_USER_URL = reverse('users:create')
TOKEN_URL = reverse('users:token')
#ME_URL = reverse('users:me')


def create_user(**params):
    return get_user_model().objects.create_user(**params)


class PublicUserApiTest(TestCase):
    """ Tests para el API de usuarios (publico) """

    def setUp(self):
        self.client = APIClient()

    def test_create_valid_user_success(self):
        """ Test creating user with valid payload is successful """

        payload = {
            'email': 'test@foodstack.mx',
            'password': 'password123',
            'name': 'Usuario de Prueba'
        }
        url = reverse('users:create')
        #print('::: URL :::')
        #print(url)

        res = self.client.post(CREATE_USER_URL, payload)
        user = get_user_model().objects.get(**res.data)

        #print('::: RESPONSE DATA :::')
        #print(res.data)

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertTrue(user.check_password(payload['password']))
        self.assertNotIn('password', res.data)


    def test_user_exists(self):
        """ Test creating a user that already exists fails """

        payload = {'email': 'test@foodstack.mx', 'password': 'password123'}
        create_user(**payload)
        res = self.client.post(CREATE_USER_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)


    def test_password_too_short(self):
        """ Test that the password must be more than 5 characters long """

        payload = {'email': 'test@foodstack.mx', 'password': 'pw'}
        res = self.client.post(CREATE_USER_URL, payload)
        user_exists = get_user_model().objects.filter(email=payload['email']).exists()

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(user_exists)



    def test_create_token_for_user(self):
        #Test that the token is created for the user

        payload = {'email': 'test@foodstack.mx', 'password': 'password123'}
        create_user(**payload)
        url = reverse('users:token')

        #print('::: URL  :::')
        #print(url)

        res = self.client.post(TOKEN_URL, payload)

        #print('::: RESPONSE DATA :::')
        #print(res.data)

        self.assertIn('token', res.data)
        self.assertEqual(res.status_code, status.HTTP_200_OK)


    def test_create_token_invalid_credentials(self):
        #Test that token is not created if invalid credentials are given

        create_user(email='test@foodstack.mx', password='password123')
        payload = {'email': 'test@foodstack.mx', 'password': 'wrong'}
        res = self.client.post(TOKEN_URL, payload)

        self.assertNotIn('token', res.data)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)


    def test_create_token_no_user(self):
        #Test that token is not created if user does not exist

        payload = {'email': 'test@foodstack.mx', 'password': 'password123'}
        res = self.client.post(TOKEN_URL, payload)

        self.assertNotIn('token', res.data)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)


    def test_create_token_missing_field(self):
        #Test that email and password are required

        res = self.client.post(TOKEN_URL, {'email': 'blablabla', 'password': ''})
        self.assertNotIn('token', res.data)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)


