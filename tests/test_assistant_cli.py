from unittest.mock import patch

from ai_agent.assistant_cli import main


@patch("ai_agent.assistant_cli.AssistantAgent")
@patch("sys.argv", ["assistant_cli.py", "--query", "Test query"])
def test_cli_query(mock_agent_class, capsys):
    mock_agent = mock_agent_class.return_value
    mock_agent.query.return_value = "Test response"
    main()
