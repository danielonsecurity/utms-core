(defunit "day"
  (length 86400)  ; Duration of a day in seconds
  (timezone 0)  ; UTC+1 timezone
  (start (round
	  (- TIMESTAMP
	     (%
	      (+ TIMESTAMP
		 self.timezone)
	      self.length)))))  ; Midnight calculation



(defunit "week7"
  (length (* 7 day.length))
  (timezone 0)
  ;; offsets for week start:
  ;; 0 - Thursday (1970-01-01 was thursday)
  ;; 1 - Friday
  ;; 2 - Saturday
  ;; 3 - Sunday
  ;; 4 - Monday
  ;; 5 - Tuesday
  ;; 6 - Wednesday
  (offset 4)
  (start
   (let [
     timezone (datetime.timezone (datetime.timedelta :seconds self.timezone))
     day-offset (get_day_of_week TIMESTAMP self day)
     current-date (datetime.datetime.fromtimestamp TIMESTAMP :tz timezone)
     midnight-today (datetime.datetime current-date.year
				       current-date.month
				       current-date.day
				       0 0 0
				       :tzinfo timezone)
     midnight-timestamp (.timestamp midnight-today)
     week-start-timestamp (- midnight-timestamp (* day-offset day.length))
     test (print TIMESTAMP day-offset current-date midnight-today)
     ]
     week-start-timestamp))
  (names ["Monday" "Tuesday" "Wednesday" "Thursday" "Friday" "Saturday" "Sunday"]))


(defunit "week7sunday"
  (length (* 7 day.length))
  (timezone 0)
  ;; offsets for week start:
  ;; 0 - Thursday (1970-01-01 was thursday)
  ;; 1 - Friday
  ;; 2 - Saturday
  ;; 3 - Sunday
  ;; 4 - Monday
  ;; 5 - Tuesday
  ;; 6 - Wednesday
  (offset 3)
  (start
   (let [
     timezone (datetime.timezone (datetime.timedelta :seconds self.timezone))
     day-offset (get_day_of_week TIMESTAMP self day)
     current-date (datetime.datetime.fromtimestamp TIMESTAMP)
     midnight-today (datetime.datetime current-date.year
				       current-date.month
				       current-date.day
				       0 0 0
				       :tzinfo timezone)
     midnight-timestamp (.timestamp midnight-today)
     week-start-timestamp (- midnight-timestamp (* day-offset day.length))
     test (print TIMESTAMP day-offset current-date midnight-today)
     ]
     week-start-timestamp))
  (names ["Sunday" "Monday" "Tuesday" "Wednesday" "Thursday" "Friday" "Saturday"]))


(defunit "week10"
  (length (* 10 day.length))
  (timezone 0)
  (offset 9)
  (start
   (let [
	reference-timestamp (* self.offset day.length)
	day-offset (get_day_of_week TIMESTAMP self day)
	current-date (datetime.datetime.fromtimestamp TIMESTAMP)
	midnight-today (datetime.datetime current-date.year
					  current-date.month
					  current-date.day
					  0 0 0)
	midnight-timestamp (.timestamp midnight-today)
	week-start-timestamp (- midnight-timestamp (* day-offset day.length))
	;; test (print TIMESTAMP total-days-elapsed day-offset current-date midnight-today)
	]
	week-start-timestamp))
  (names ["Firstday" "Secondday" "Thirdday" "Fourthday" "Fifthtday" "Sixthday" "Sevenday" "Eigthday" "Nineday" "Tenday"]))






(defunit "month"
    (timezone 0)
    (length (let [timezone (datetime.timezone (datetime.timedelta :seconds self.timezone))
		 now (datetime.datetime.fromtimestamp TIMESTAMP :tz timezone)]
		 (let [next-month
		   (if (= now.month 12)
		       (datetime.datetime (+ now.year 1) 1 1)
		       (datetime.datetime now.year (+ now.month 1) 1))]
		   (- (.timestamp next-month)
		      (.timestamp (datetime.datetime now.year now.month 1))))))

  (start
   (let [
	timezone (datetime.timezone (datetime.timedelta :seconds self.timezone))
	now (datetime.datetime.fromtimestamp TIMESTAMP :tz timezone)
	midnight (datetime.datetime now.year now.month 1 :tzinfo timezone)]
	(.timestamp midnight))
   )
  )

(defunit "year"
    (length
     (let [timezone (datetime.timezone (datetime.timedelta :seconds self.timezone))
	  current-date (datetime.datetime.fromtimestamp TIMESTAMP :tz timezone)
          next-year (datetime.datetime (+ current-date.year 1) 1 1 :tzinfo timezone)
          this-year (datetime.datetime current-date.year 1 1 :tzinfo timezone)]
	  (- (.timestamp next-year) (.timestamp this-year))))
  (timezone 0)
  (start
   (let [timezone (datetime.timezone (datetime.timedelta :seconds self.timezone))
	current-date (datetime.datetime.fromtimestamp TIMESTAMP :tz timezone)]
	(.timestamp (datetime.datetime current-date.year 1 1 :tzinfo timezone))))
  (names ["January" "February" "March" "April" "May" "June" "July" "August" "September" "October" "November" "December"])
  (index (let [timezone (datetime.timezone (datetime.timedelta :seconds self.timezone))
	   current-date (datetime.datetime.fromtimestamp TIMESTAMP :tz timezone)]
	      (- current-date.month 1))))
