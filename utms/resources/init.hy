;; test.hy

;; Config storage
(setv config-data {})
(setv config-defaults {})

;; Basic setter macro
(defmacro setconfig [name value]
  `(setv (get config-data ~name) ~value))

;; Define default value with documentation
(defmacro defconfig [name default type group doc]
  `(do
     (setv (get config-defaults ~name) 
           {:value ~default 
            :type ~type 
            :group ~group 
            :doc ~doc})
     (when (not (in ~name config-data))
       (setv (get config-data ~name) (get config-defaults ~name)))))

;; Helper to get config value with fallback to default
(defn get-config [name]
  (let [entry (or (get config-data name)
                 (get config-defaults name))]
    (if (isinstance entry dict)
      (get entry :value)
      entry)))

;; Define defaults first
(defconfig "gemini-model" 
          "gemini-1.5-pro"
          str 
          "gemini"
          "Model to use for text generation")

(defconfig "gemini-top-p" 
          0.5 
          float 
          "gemini"
          "Top-p sampling parameter (higher = more random)")

(defconfig "gemini-max-tokens" 
          100 
          int 
          "gemini"
          "Maximum number of tokens in response")

;; Override some defaults
(setconfig "gemini-model" "gemini-1.5-flash")
(setconfig "gemini-top-p" 0.7)

;; Improved print function showing defaults
(defn print-config []
  (print "\nCurrent configuration:")
  (for [k (.keys config-defaults)]
    (let [current (get-config k)
          meta (get config-defaults k)
          default (get meta :value)]
      (print f"  {k}: {current}"
            (if (!= current default) 
                f" (default: {default})"
                "")  ; empty string if value equals default
            f"\n    type: {(get meta :type)}"
            f"\n    group: {(get meta :group)}"
            f"\n    doc: {(get meta :doc)}"))))

;; Print group with documentation and defaults
(defn print-group [group-name]
  (print f"\nSettings for group '{group-name}':")
  (for [k (.keys config-defaults)]
    (let [meta (get config-defaults k)]
      (when (= (get meta :group) group-name)
        (let [current (get-config k)
              default (get meta :value)]
          (print f"  {k}: {current}"
                (if (!= current default)
                    f" (default: {default})"
                    "")  ; empty string if value equals default
                f"\n    {(get meta :doc)}"))))))

;; Print all config and then gemini group
(print-config)
(print-group "gemini")
