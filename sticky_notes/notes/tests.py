from django.test import TestCase
from django.urls import reverse
from notes.models import Note
# Absolute import to ensure correct module resolution
from notes.forms import NoteForm


class NoteModelTest(TestCase):
    """
    Tests the Note model.
    """
    def test_note_creation(self):
        """
        Test if a Note object is created successfully.
        """
        note = Note.objects.create(
            title="Test Note",
            content="This is a test note."
        )
        self.assertEqual(note.title, "Test Note")
        self.assertEqual(note.content, "This is a test note.")


class NoteFormTest(TestCase):
    """
    Tests the NoteForm.
    """
    def test_note_form_valid(self):
        """
        Test that the form is valid with correct data.
        """
        form_data = {'title': 'Test Form', 'content': 'This is a test form.'}
        form = NoteForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_note_form_invalid(self):
        """
        Test that the form is invalid with missing data.
        """
        form_data = {'title': 'Test Form'}  # Missing content
        form = NoteForm(data=form_data)
        self.assertFalse(form.is_valid())


class NoteViewTest(TestCase):
    """
    Tests the views of the application.
    """
    def setUp(self):
        """
        Set up a Note object for testing.
        """
        self.note = Note.objects.create(
            title="Test View Note",
            content="Test content."
        )

    def test_note_list_view(self):
        """
        Test the note_list view.
        """
        response = self.client.get(reverse('note_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Test View Note")

    def test_note_create_view(self):
        """
        Test the note_create view.
        """
        response = self.client.get(reverse('note_create'))
        self.assertEqual(response.status_code, 200)

    def test_note_update_view(self):
        """
        Test the note_update view.
        """
        response = self.client.get(reverse('note_update', args=[self.note.pk]))
        self.assertEqual(response.status_code, 200)

    def test_note_delete_view(self):
        """
        Test the note_delete view.
        """
        response = self.client.get(reverse('note_delete', args=[self.note.pk]))
        self.assertEqual(response.status_code, 200)
