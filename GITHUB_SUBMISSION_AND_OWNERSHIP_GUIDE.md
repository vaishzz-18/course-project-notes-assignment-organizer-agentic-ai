# GitHub Repository Submission & Ownership Transfer Guide

## Team 14 — Artifact: Course Project, Notes & Assignment Organizer (apniLeap AURA)

---

### Step 1: Create a Completely New Repository on GitHub
1. Log in to your GitHub account ([github.com](https://github.com)).
2. In the top-right corner, click **+** and select **New repository**.
3. Set the repository name to:
   ```text
   course-project-notes-assignment-organizer
   ```
4. Choose **Public** (or **Private** as required by your instructor).
5. **IMPORTANT**: Do **NOT** check "Add a README file", "Add .gitignore", or "Choose a license" (we already have all of these prepared).
6. Click **Create repository**.
7. Copy your new repository URL:
   `https://github.com/<YOUR_GITHUB_USERNAME>/course-project-notes-assignment-organizer.git`

---

### Step 2: Initialize & Push from Your Local Terminal
Open your **PowerShell** or **Command Prompt** as your user in this project folder (`D:\Sem 7\AGENTIC AI\PROJ\AGENTICAIAG1 new proj`) and run:

```powershell
# 1. Initialize a fresh Git repository
git init -b main

# 2. Add all project files (ignoring .env and secrets automatically via .gitignore)
git add .

# 3. Create your initial commit
git commit -m "feat: complete academic submission package for Team 14 (AURA Chapter 2)"

# 4. Link to your brand new GitHub repository
git remote add origin https://github.com/<YOUR_GITHUB_USERNAME>/course-project-notes-assignment-organizer.git

# 5. Push the code to GitHub
git push -u origin main
```

---

### Step 3: Transfer Repository Ownership (If Requested by Professor)
If your professor requires transferring the repository to a course organization:
1. Navigate to your repository on GitHub.
2. Click **Settings** (tab at the top right of the repo).
3. Scroll down to the **Danger Zone** at the bottom.
4. Click **Transfer ownership**.
5. Enter the target GitHub Organization username provided by your professor.
6. Type the repository name to confirm and click **I understand, transfer this repository**.
7. Confirm that you retain Admin or Write access to the repository under the organization.

---

### Step 4: Submit the Repository Details
Copy the repository URL and paste it into the professor's approval form alongside the details listed in `SUBMISSION_FORM_DETAILS.md`.
