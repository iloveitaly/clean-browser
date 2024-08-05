import datetime
import os
import unittest
from unittest.mock import patch, MagicMock
from clean_workspace.archive import archive_old_tasks

class TestArchiveOldTasks(unittest.TestCase):

    @patch('clean_workspace.archive.TodoistAPI')
    @patch('clean_workspace.archive.datetime')
    @patch.dict(os.environ, {'TODOIST_API_KEY': 'test_key'})
    def test_archive_old_tasks(self, mock_datetime, MockTodoistAPI):
        mock_api = MockTodoistAPI.return_value
        mock_task = MagicMock()
        mock_task.created_at = (datetime.datetime.now() - datetime.timedelta(days=366)).strftime("%Y-%m-%dT%H:%M:%S.%fZ")
        mock_task.content = "Test Task"
        mock_task.project_id = 123
        mock_api.get_tasks.return_value = [mock_task]

        mock_datetime.datetime.now.return_value = datetime.datetime(2023, 1, 1)

        archive_old_tasks()

        mock_api.add_task.assert_called_once_with(content="# 2022-01-01\n\nTest Task", project_id=123)
        mock_api.close_task.assert_called_once_with(mock_task.id)

if __name__ == '__main__':
    unittest.main()
