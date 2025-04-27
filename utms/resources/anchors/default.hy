(def-anchor BIGBANG
  (name "Big Bang Time (13.8e9 years ago)")
  (value -435485579904000000)
  (formats [{:units ["Y"]} "UNITS" {:format "SCIENTIFIC" :options {:notation "scientific" :show_uncertainty "true"}}])
  (groups ["astronomical" "fixed" "test"])
)

(def-anchor HUMANERA
  (name (+ "Human Era (" (str (+ current-year 10000)) " years ago)"))
  (value -377736414526)
  (formats [{:units ["Y"]} {:units ["d"]} {:units ["Y" "d" "h" "m" "s"]}])
  (groups ["astronomical" "fixed"])
)

(def-anchor JULIAN
  (name "Julian Date")
  (value -210866760000)
  (formats [["Y"] ["s"] ["d"] "UNITS" "DATETIME" "SCIENTIFIC" {:format "UNITS" :units ["Y" "M" "d" "dd" "cd" "s"]}])
  (groups ["default" "dynamic" "historical" "astronomical"])
)

(def-anchor CETIME
  (name "CE Time (0001-01-01 00:00:00)")
  (value -62167153726)
  (formats [["Y"] ["s"] "UNITS" "DATETIME" "SCIENTIFIC" {:format "UNITS" :units ["Y" "M" "d" "dd" "cd" "s"]}])
  (groups ["default" "historical"])
)

(def-anchor UNIX
  (name "Unix Time")
  (value 0)
  (formats ["CALENDAR" ["Y"] ["s"] {:format "UNITS"}])
  (groups ["standard" "default" "modern"])
  (uncertainty {:absolute 1e-09 :relative 1e-09})
)

(def-anchor MILLENIUM
  (name "Millenium Time (2000-01-01 00:00:00)")
  (value millenium-start)
  (formats [["Y"] ["s"] "UNITS" "DATETIME" "SCIENTIFIC"])
  (groups ["default" "dynamic" "modern"])
)

(def-anchor YEARTIME
  (name (+ "Year Time (" (. current-time strftime "%Y-01-01 00:00:00") ")"))
  (value year-start)
  (formats [["Y"] ["s"] ["d"] "UNITS" "DATETIME" "SCIENTIFIC" {:format "UNITS" :units ["Y" "M" "d" "dd" "cd" "s"]}])
  (groups ["default" "dynamic" "modern"])
)

(def-anchor MONTHTIME
  (name (+ "Month Time (" (. current-time strftime "%Y-%m-01 00:00:00") ")"))
  (value month-start)
  (formats [["Y"] ["s"] "UNITS" "DATETIME" {:format "SCIENTIFIC" :options {:notation "scientific"}} {:format "UNITS" :units ["Y" "M" "d" "dd" "cd" "s"]}])
  (groups ["default" "dynamic" "modern"])
)

(def-anchor DAYTIME
  (name (+ "Day Time (UTC " (. current-time strftime "%Y-%m-%d 00:00:00") ")"))
  (value day-start)
  (formats [["Y"] ["s"] "UNITS" "SCIENTIFIC" "DATETIME" {:format "UNITS" :units ["Y" "d" "dd" "cd" "s"]}])
  (groups ["default" "dynamic" "modern"])
)

(def-anchor NOW
  (name (+ "NOW Time (UTC " (. current-time strftime "%Y-%m-%d %H:%M:%S") ")"))
  (value current-time)
  (formats ["SCIENTIFIC" ["Y"] ["s"] "UNITS"])
  (groups ["default" "dynamic" "modern"])
)
