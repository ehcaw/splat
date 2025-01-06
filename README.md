# splat
splat is a tool that combines your compile/runtime errors and grabs context from every crevice to deliver a highly educated debug response. This is perfect for whenever you have an error that needs to be quickly fixed, understood, and prevented for later in the future.
created at calhacks 11.0
 /\_/\
( o.o )
 > ^ <
## Features
- **AI-Optimized**: We use an extremely fast inference model [Groq](https://groq.com/) in order to produce an instant debug error, with still the same amount of accuracy.
- **Simple to Use**: <ins>splat</ins> can be used out-of-the-box and globally in any project without any configuration.
- **Git Aware**: <ins>splat</ins> takes into consideration your .gitignore files so that we won't use any sensitive info.
- **Highly Contextual**: You can use <ins>splat</ins> with a `-r` flag, grabbing all nodes to the Nth degree related to all error stack files in order to grab the most related content, delivering a highly accurate, optimized, and contextual debug response.

## Known Bugs
- <ins>splat</ins> will not conform to any formatting configurations when inserting code
- <ins>splat</ins> does not do well with running sub-module entrypoints that do not originate in the root directory
  
## Quick Start
You can use <ins>splat</ins> out of the box:  

`splat squash <?-r> <!entrypoint>`.

Example:
Just like you would enter your app, do so with <ins>splat</ins>.  

`splat squash "python3 foo.py"`

`splat squash -r "python3 main.py"`

And that's it!
