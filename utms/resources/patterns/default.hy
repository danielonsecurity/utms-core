;; Simple patterns
(def-pattern DAILY-STANDUP
  (name "Daily Standup")
  (every "1d")
  (at "10:00")
  (on ["monday" "tuesday" "wednesday" "thursday" "friday"])
)

(def-pattern LUNCH-BREAK
  (name "Lunch Break")
  (every "1d")
  (between "12:00" "13:00")
  (on ["monday" "tuesday" "wednesday" "thursday" "friday"])
)

;; Complex patterns
(def-pattern COMPLEX-MEETING
  (name "Complex Team Meeting")
  (every "2h + 15m")
  (between "9:00" "17:00")
  (on ["monday" "wednesday"])
  (except-between "12:00" "13:00")
)

;; Multiple times pattern
(def-pattern STATUS-UPDATES
  (name "Status Updates")
  (every "1d")
  (at ["9:00" "14:00" "16:30"])
  (on ["monday" "wednesday" "friday"])
)

;; Business hours pattern
(def-pattern BUSINESS-HOURS
  (name "Business Hours Check")
  (every "30m")
  (between "9:00" "17:00")
  (on ["monday" "tuesday" "wednesday" "thursday" "friday"])
  (except-between "12:00" "13:00")
  (groups ["business" "monitoring"])
)

;; Weekend pattern
(def-pattern WEEKEND-BACKUP
  (name "Weekend Backup")
  (every "12h")
  (at "3:00" "15:00")
  (on ["saturday" "sunday"])
  (groups ["maintenance" "backup"])
)
