on run argv
  set inPath to item 1 of argv
  set outPath to item 2 of argv
  tell application "Microsoft PowerPoint"
    open (POSIX file inPath)
    set pres to active presentation
    save pres in (POSIX file outPath) as save as PDF
    close pres saving no
  end tell
end run
