# Feedback analytics overview

- `summary.json`/`summary.md` — автоматически перегенерируются после каждой
  отправки через `FeedbackService` или при запуске `tools/feedback_sync.py summary`.
- Очередь неподтверждённых отчётов хранится в `inbox.jsonl` (создаётся при первом
  сабмите) и обрабатывается утилитой `tools/feedback_sync.py push`.
- История выгрузок фиксируется в `sent.log` (не коммитим в репозиторий).

