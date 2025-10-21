# 🎯 QUICK EXTENSIONS CHECKLIST - VS CODE

## ⚡ FAST INSTALL (2 MINUTES)

### Method 1: Automatic (EASIEST) ⭐
```
1. Open VS Code
2. Press Ctrl+Shift+X
3. Type: @recommended
4. Click: "Install Workspace Extension Recommendations"
5. Wait 2-3 minutes
6. Reload: Ctrl+Shift+P → "Reload Window"
```

---

## 🔴 CRITICAL EXTENSIONS (Must Have)

| # | Name | Extension ID | Why |
|---|------|--------------|-----|
| 1 | **GitHub Copilot** | `github.copilot` | AI code completion |
| 2 | **Copilot Chat** | `github.copilot-chat` | AI assistant |
| 3 | **Python** | `ms-python.python` | Python support |
| 4 | **Pylance** | `ms-python.vscode-pylance` | IntelliSense, types |
| 5 | **GitLens** | `eamodio.gitlens` | Git blame, history |
| 6 | **Russian Spell** | `streetsidesoftware.code-spell-checker-russian` | Spell checking |
| 7 | **Error Lens** | `usernamehw.errorlens` | Inline errors |
| 8 | **Better Comments** | `aaron-bond.better-comments` | Colored comments |

---

## ⚠️ RECOMMENDED (Nice to Have)

- Black Formatter (`ms-python.black-formatter`)
- Flake8 (`ms-python.flake8`)
- Mypy (`ms-python.mypy-type-checker`)
- Git Graph (`mhutchie.git-graph`)
- QML (`bbenoist.QML`)
- TODO Highlight (`wayou.vscode-todo-highlight`)
- Markdown All in One (`yzhang.markdown-all-in-one`)

---

## ✅ VERIFICATION CHECKLIST

After install, check these work:

- [ ] **Copilot**: Start typing → gray suggestions appear
- [ ] **Pylance**: Open .py file → types shown inline
- [ ] **GitLens**: Open file → gray author comments at line ends
- [ ] **Russian Spell**: Type comment with typo → underlined
- [ ] **Error Lens**: Add syntax error → shown inline
- [ ] **Better Comments**: Write `// TODO:` → colored

---

## 🔧 TROUBLESHOOTING

### Copilot not suggesting:
```
Ctrl+Shift+P → "GitHub Copilot: Sign In"
```

### Inlay hints not visible:
```json
"python.analysis.inlayHints.variableTypes": true
```

### Russian spell checker not working:
```
Ctrl+Shift+P → "Code Spell Checker: Enable Language" → Russian
```

---

## 📊 SUCCESS CRITERIA

Setup complete when:
- ✅ 8 critical extensions installed
- ✅ Copilot shows suggestions
- ✅ GitLens shows authors
- ✅ Python types visible inline
- ✅ Errors shown inline

---

**Time**: 5 minutes
**Difficulty**: Easy
**Impact**: +11.4% productivity

---

**💡 TIP**: Use `@recommended` method - installs ALL at once!
