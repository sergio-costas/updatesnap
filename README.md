# updatesnap

A simple script that checks a snapcraft yaml file and shows possible new versions for each part

## Using it

Just run *updatesnap.py /path/to/snapcraft.yaml*. Optionally, you can add a Part name, and updatesnap
will check only that part, instead of all.

The output is like this:

```
  Part: glib (https://gitlab.gnome.org/GNOME/glib.git)  
    Current branch: glib-2-72  
    Current version: 2.72  
    Newer branches  
      mcatanzaro/glib-2-68-rhel9  
      mcatanzaro/glib-2-56-rhel8  
      mcatanzaro/#2597  
      mcatanzaro/#1346  
      main-c89  
      262.c89  
    Alternative tags  
      GLIB_1_2_9PRE3  
      EAZEL-NAUTILUS-MS-AUG07  
      2.73.0  
      2.72.2  
      2.72.1  
      2.72.0  
```

The first line contains the part name and the repository URI.
The second line contains the current branch or tag configured in the YAML file
The third line contains the parsed version: since there isn't a standard for versions
in tags or branches, updatesnap has to use heuristics to extract it.

Then it comes a list of branches whose extracted version number is equal or greater
than the current one. After that, comes a list of tags with a version number equal or
greater than the current one.

In this example, glib is being compiled from the branch glib-2-72, and there isn't a
bigger version branch. There is a tag called 2.73.0, so we can choose to use it in
the snapcraft file.

## The .secrets file

Optionally it is possible to configure a YAML file named *updatesnap.secrets* and put it
at *~/.config/updatesnap/*. This file can contain a Github username and token to
avoid the access limits that Github imposes to anonymous API requests. The format
is the following:

github:
    user: *username*
    token: *github access token*
