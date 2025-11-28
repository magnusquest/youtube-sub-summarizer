# Task: Project Setup & Configuration

## Objective
Establish project structure, dependencies, and configuration management for the YouTube subscription summarizer.

## Acceptance Criteria
- [ ] Python virtual environment created and activated
- [ ] All required dependencies installed via `requirements.txt`
- [ ] `.env` file template created with all necessary API keys
- [ ] `.gitignore` configured to exclude secrets and generated files
- [ ] Project directory structure follows best practices
- [ ] Configuration can be loaded from environment variables
- [ ] README.md includes setup instructions

## Implementation Approach
1. Create Python virtual environment
2. Define `requirements.txt` with:
   - `google-api-python-client`
   - `youtube-transcript-api`
   - `openai`
   - `python-dotenv`
3. Create `.env.example` template
4. Create basic project structure:
   ```
   youtube-sub-summarizer/
   ├── src/
   │   ├── __init__.py
   │   ├── config.py          # Load environment variables
   │   ├── youtube_client.py
   │   ├── transcript.py
   │   ├── summarizer.py
   │   ├── email_sender.py
   │   ├── database.py
   │   └── main.py
   ├── data/
   │   └── processed_videos.db
   ├── logs/
   ├── .env.example
   ├── .gitignore
   ├── requirements.txt
   └── README.md
   ```

## Dependencies
- Blocked by: None (first task)
- Blocks: All other tasks
- Requires: Python 3.9+

## Estimated Effort
1-2 hours

## Subtasks
1. [ ] Create virtual environment: `python3 -m venv venv`
2. [ ] Create `requirements.txt` with all dependencies
3. [ ] Create `.env.example` with all required variables
4. [ ] Create `.gitignore` (include `.env`, `venv/`, `*.db`, `logs/`)
5. [ ] Create project directory structure
6. [ ] Write `src/config.py` to load environment variables
7. [ ] Update README.md with setup instructions

## Notes
- Use `python-dotenv` to keep secrets out of code
- Consider adding logging configuration early
- `.env.example` should have placeholder values, not real keys
