import datetime
from django.test import TestCase
from rest_framework import serializers
from rest_framework.tests.models import *


class Comment(object):
    def __init__(self, email, content, created):
        self.email = email
        self.content = content
        self.created = created or datetime.datetime.now()

    def __eq__(self, other):
        return all([getattr(self, attr) == getattr(other, attr)
                    for attr in ('email', 'content', 'created')])


class CommentSerializer(serializers.Serializer):
    email = serializers.EmailField()
    content = serializers.CharField(max_length=1000)
    created = serializers.DateTimeField()

    def restore_object(self, data, instance=None):
        if instance is None:
            return Comment(**data)
        for key, val in data.items():
            setattr(instance, key, val)
        return instance


class BasicTests(TestCase):
    def setUp(self):
        self.comment = Comment(
            'tom@example.com',
            'Happy new year!',
            datetime.datetime(2012, 1, 1)
        )
        self.data = {
            'email': 'tom@example.com',
            'content': 'Happy new year!',
            'created': datetime.datetime(2012, 1, 1)
        }

    def test_empty(self):
        serializer = CommentSerializer()
        expected = {
            'email': '',
            'content': '',
            'created': None
        }
        self.assertEquals(serializer.data, expected)

    def test_serialization(self):
        serializer = CommentSerializer(instance=self.comment)
        expected = self.data
        self.assertEquals(serializer.data, expected)

    def test_deserialization_for_create(self):
        serializer = CommentSerializer(self.data)
        expected = self.comment
        self.assertEquals(serializer.is_valid(), True)
        self.assertEquals(serializer.object, expected)
        self.assertFalse(serializer.object is expected)

    def test_deserialization_for_update(self):
        serializer = CommentSerializer(self.data, instance=self.comment)
        expected = self.comment
        self.assertEquals(serializer.is_valid(), True)
        self.assertEquals(serializer.object, expected)
        self.assertTrue(serializer.object is expected)


class ValidationTests(TestCase):
    def setUp(self):
        self.comment = Comment(
            'tom@example.com',
            'Happy new year!',
            datetime.datetime(2012, 1, 1)
        )
        self.data = {
            'email': 'tom@example.com',
            'content': 'x' * 1001,
            'created': datetime.datetime(2012, 1, 1)
        }

    def test_deserialization_for_create(self):
        serializer = CommentSerializer(self.data)
        self.assertEquals(serializer.is_valid(), False)
        self.assertEquals(serializer.errors, {'content': [u'Ensure this value has at most 1000 characters (it has 1001).']})

    def test_deserialization_for_update(self):
        serializer = CommentSerializer(self.data, instance=self.comment)
        self.assertEquals(serializer.is_valid(), False)
        self.assertEquals(serializer.errors, {'content': [u'Ensure this value has at most 1000 characters (it has 1001).']})


class MetadataTests(TestCase):
    def test_empty(self):
        serializer = CommentSerializer()
        expected = {
            'email': serializers.CharField,
            'content': serializers.CharField,
            'created': serializers.DateTimeField
        }
        for field_name, field in expected.items():
            self.assertTrue(isinstance(serializer.data.fields[field_name], field))


class ManyToManyTests(TestCase):
    def setUp(self):
        class ManyToManySerializer(serializers.ModelSerializer):
            class Meta:
                model = ManyToManyModel

        self.serializer_class = ManyToManySerializer

        # An anchor instance to use for the relationship
        self.anchor = Anchor()
        self.anchor.save()

        # A model instance with a many to many relationship to the anchor
        self.instance = ManyToManyModel()
        self.instance.save()
        self.instance.rel.add(self.anchor)

        # A serialized representation of the model instance
        self.data = {'id': 1, 'rel': [self.anchor.id]}

    def test_retrieve(self):
        serializer = self.serializer_class(instance=self.instance)
        expected = self.data
        self.assertEquals(serializer.data, expected)

    def test_create(self):
        data = {'rel': [self.anchor.id]}
        serializer = self.serializer_class(data)
        self.assertEquals(serializer.is_valid(), True)
        serializer.object.save()
        obj = serializer.object.object
        self.assertEquals(obj.pk, 2)
        self.assertEquals(list(obj.rel.all()), [self.anchor])
        # self.assertFalse(serializer.object is expected)

    # def test_deserialization_for_update(self):
    #     serializer = self.serializer_class(self.data, instance=self.instance)
    #     expected = self.instance
    #     self.assertEquals(serializer.is_valid(), True)
    #     self.assertEquals(serializer.object, expected)
    #     self.assertTrue(serializer.object is expected)