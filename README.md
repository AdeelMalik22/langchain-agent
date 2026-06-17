# AI Agent with Tool Integration

An intelligent AI agent built with LangChain that leverages the Nemotron-3 reasoning model from OpenRouter. The agent can perform various tasks including mathematical operations, GitHub repository exploration, and Gmail email management.

## Features

### Mathematical Tools
- **multiply**: Multiply two numbers
- **divide**: Divide two numbers (with zero-division protection)
- **add**: Add two numbers
- **subtract**: Subtract two numbers

### GitHub Tools
- **github_repos**: Explore GitHub user profiles and list all public repositories with details including:
  - Repository name and description
  - Primary programming language
  - Star count
  - Repository URL

#### Advanced GitHub API Tools (requires GITHUB_TOKEN)
- **github_user**: Manage GitHub user/account info (profile, details, repos)
- **github_repository**: Manage repository info (details, contents, tags, compare)
- **github_branch**: Manage branches (list, create, delete)
- **github_file**: Manage files in a repo (read, create/update, delete)
- **github_commit**: View commit history and details
- **github_issue**: Manage issues (list, get, create, update, comment)
- **github_pull_request**: Manage pull requests (list, get, create, comment, review, merge)
- **github_search**: Search GitHub (repos, code, issues)
- **github_workflow**: Manage GitHub Actions workflows (list, runs, trigger, status)

### Gmail Tools
- **gmail_read**: Retrieve the latest emails from your Gmail inbox
- **gmail_search**: Search Gmail emails by sender or subject
- **gmail_save_draft**: Create and save email drafts without sending

## Prerequisites

- Python 3.8+
- OpenRouter API key
- GitHub Personal Access Token (for GitHub API tools)
- Gmail credentials (for email features)

## Installation

**For detailed setup instructions, see [SETUP.md](./SETUP.md)**

1. Clone the repository:
```bash
git clone <repository-url>
cd agent
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Create a `.env` file in the project root with the following variables:
```
OPENROUTER_API_KEY=your_openrouter_api_key
GITHUB_TOKEN=your_github_personal_access_token
GMAIL_ADDRESS=your_gmail_address
GMAIL_APP_PASSWORD=your_gmail_app_password
```

**Note:** See [SETUP.md](./SETUP.md) for detailed instructions on how to obtain these credentials.

### Gmail Setup Notes
- For Gmail integration, you'll need to generate an [App Password](https://myaccount.google.com/apppasswords) instead of using your regular Gmail password
- Ensure "Less secure app access" is enabled if required by your Gmail settings

### GitHub Setup Notes
- For GitHub integration, you'll need to create a [Personal Access Token](https://github.com/settings/tokens) with appropriate scopes:
  - `repo` - Full control of private repositories (for creating branches, PRs, etc.)
  - `public_repo` - Access to public repositories
  - `workflow` - Full control of workflows and actions
- Set the `GITHUB_TOKEN` environment variable with your token

## Usage

Run the agent in interactive mode:
```bash
python main.py
```

The agent will start a conversation loop where you can:
1. Ask questions or give commands
2. The AI agent will automatically:
   - Analyze your request
   - Use the appropriate tools needed
   - Execute tools and process results
   - Provide a comprehensive answer

3. Type `exit` or `quit` to end the session, or use `Ctrl+C`

### Example Interactions
- "What is 25 multiplied by 4?"
- "Show me the repositories for the GitHub user AdeelMalik22"
- "In the langchain-agent repo, create a branch called qa from master"
- "Create a pull request from qa to master branch with title 'QA Testing' and body 'Quality assurance testing'"
- "List all issues in the langchain-agent repo"
- "Read my latest 3 emails from Gmail"
- "Search for emails from john@example.com"
- "Save a draft email to alice@example.com with subject 'Meeting' and body 'Let's meet tomorrow'"

## Project Structure

```
agent/
├── main.py                    # Main agent entry point and chat loop
├── tools.py                   # Tool definitions and implementations
├── github_client.py           # GitHub API tools and utilities
├── requirements.txt           # Python dependencies
├── .env                       # Environment variables (create this yourself)
├── README.md                  # Project overview and usage guide
├── SETUP.md                   # Detailed setup and configuration guide
├── GITHUB_TOOLS.md            # GitHub tools detailed documentation
└── __pycache__/               # Python cache directory
```

## How It Works

1. **Initialization**: The agent initializes with the Nemotron-3 model from OpenRouter
2. **Tool Binding**: All available tools are bound to the model
3. **Message Loop**: 
   - User query is converted to a HumanMessage
   - Model processes the query and decides which tools to use
   - Tools are executed with the model's arguments
   - Tool results are fed back to the model
   - Process repeats until the model has a final answer
4. **Response**: The final answer is presented to the user

## Dependencies

Key dependencies include:
- **langchain**: LLM framework for building AI agents
- **langchain-openrouter**: Integration with OpenRouter API
- **requests**: HTTP library for GitHub API calls
- **python-dotenv**: Environment variable management
- **imaplib/smtplib**: Gmail integration for email operations

## Error Handling

The agent includes error handling for:
- Unknown tools
- GitHub API errors (non-existent users, rate limits)
- Gmail authentication failures
- Division by zero
- Invalid email search parameters

## Configuration

The agent uses the following configuration:
- **Model**: `nvidia/nemotron-3-nano-omni-30b-a3b-reasoning:free` via OpenRouter
- **Temperature**: 0 (deterministic responses)
- **Tool Integration**: Automatic tool binding and execution

## License

This project is open source and available under the MIT License.

## Support and Documentation

### Quick Links
- **[SETUP.md](./SETUP.md)** - Step-by-step setup instructions with API key generation
- **[GITHUB_TOOLS.md](./GITHUB_TOOLS.md)** - Detailed GitHub tools documentation with examples
- **[TROUBLESHOOTING.md](./TROUBLESHOOTING.md)** - Common issues and solutions

### Getting Help
1. Check the relevant documentation file above
2. Verify that all environment variables are properly set in `.env`
3. See [TROUBLESHOOTING.md](./TROUBLESHOOTING.md) for common issues
4. Check tool error messages for specific issues
5. Enable debug logging for more detailed information

## Contributing

Contributions are welcome! To add new tools:
1. Define the tool function in `tools.py` with the `@tool` decorator
2. Add it to the `ALL_TOOLS` list
3. Add it to the `TOOL_MAP` dictionary
4. Update this README with the new tool documentation

#comment for testing