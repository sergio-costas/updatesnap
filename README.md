# updatesnap

A simple script that checks a snapcraft yaml file and shows possible new versions for each part

## Using it

Just run *updatesnap.py [-s] [-r] /path/to/snapcraft.yaml*. Optionally, you can add a Part name, and updatesnap
will check only that part, instead of all.

The output is like this:

```
  Part: libsoup3 (https://gitlab.gnome.org/GNOME/libsoup.git)
    Current tag: 3.0.6
    Current tag date: 2022-03-31 13:33:55-05:00
    Tag updated

  Part: librest (https://gitlab.gnome.org/GNOME/librest.git)
    Current tag: 0.8.1
    Current tag date: 2017-05-12 10:16:04+02:00
    Newer tags:
      0.9.1 (2022-06-19 12:28:19+02:00)
      0.9.0 (2022-01-12 19:15:20+00:00)
      1.0.0 (2022-01-12 19:15:20+00:00)

  Part: gtk3 (https://gitlab.gnome.org/GNOME/gtk.git)
    Current tag: 3.24.34
    Current tag date: 2022-05-18 14:52:03-04:00
    Newer tags:
      4.6.5 (2022-05-30 16:26:00-04:00)

```

The first line contains the part name and the repository URI.
The second line contains the current branch or tag configured in the YAML file.
If this part uses a branch, it will recommend to switch to an specific tag.
The third line contains the date that the current tag was uploaded.
After that it can be a "Tag updated" text, which means that there are
no tags more recent that the current one, or the text "Newer tags", and
a list of all the tags pushed more recently than the current one.

In this example, libsoup3 is fully updated, librest has three newer tags,
but they seems to be a new major version (1.0.0) and a development version
(0.9.0 and 0.9.1), and Gtk3 has a newer tag, but it is for Gtk4, so we
must ignore it.

Setting the *-r* parameter, it won't search for a *snapcraft.yaml* file in
the specified folder, but will search it in each folder inside that folder.
This is useful when you have an specific folder with several *snap* projects,
each one in its own folder, and want to check all of them.

## The .secrets file

Optionally it is possible to configure a YAML file named *updatesnap.secrets* and put it
at *~/.config/updatesnap/*. This file can contain a Github username and token to
avoid the access limits that Github imposes to anonymous API requests. The format
is the following:

## TODO

* Migrate to specific github and gitlab modules instead of using custom code
* Add version parsing capabilities to automatize it even further
  * List only newer versions
  * Add limits to major/minor version numbers (for parts that can't be compiled with too new versions of other parts)
  * Add odd/even detection for cases where odd minor numbers are development versions
* Automagically generate an updated *snapcraft.yaml* file

github:  
    user: *username*  
    token: *github access token*
