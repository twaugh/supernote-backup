# SupernoteCloud package

## Submodules

## SupernoteCloud module

## Module contents

### *class* SupernoteCloud.Client(username, password)

Bases: `object`

Supernote Cloud client class

This class provides methods for interacting with Supernote Cloud. It provides
an interface similar to a filesystem, including methods which act
similarly to os.walk(), as well as for uploading and downloading files,
and fetching metadata.

Because Supernote Cloud files and folders can use “/” in their names,
methods are provided to make these usable as local filenames (by quoting).

Files and folders can be referenced using their unique identifiers,
or by full “/”-separated pathname (if they have previously been seen).

#### download_file_id(ident, filename)

Download the file with identifier ident to the local file named filename.

#### download_file_path(path, filename)

Download the file named path to the local file named filename.

#### *classmethod* quote(path)

Convert a Supernote-native filename into a pathname.

#### stat_id(ident)

Get metadata for the file with the given identifier ident.

#### stat_path(path)

Get metadata for the filename at path.

#### upload_file_id(src, ident=0)

Upload the file named src to the folder with identifier ident.

#### upload_file_path(src, dstpath='')

Upload the file named src to the folder at path dstpath.

#### walk()

Find available files and folders by walking the folder tree from
the top.

This behaves similarly to os.path.walk().

For each folder in the cloud account rooted at the given path (and
including that path), yield a 3-tuple:

```default
folder_path, folder_names, file_names
```

folder_path is a string, the full path to the folder. Each folder
is separated by ‘/’. If the folder name includes ‘/’ it becomes ‘%2F’.
folder_names is a list of the folders contained at that path.
file_names is a list of the files contained at that path.

#### walk_id(ident=0)

Find available files and folders by walking the folder
tree. If an identifier is given, start at the folder with that
identifier. Otherwise start at the top. The top folder must have
been returned by a previous call to one of the walk methods.

This behaves similarly to os.path.walk(), starting at the path
indicated by the identifier ident.

For each folder in the cloud account rooted at the given identifier
(and including that path), yield a 3-tuple:

```default
folder_path, folder_names, file_names
```

folder_path is a string, the full path to the folder. Each folder
is separated by ‘/’. If the folder name includes ‘/’ it becomes ‘%2F’.
folder_names is a list of the folders contained at that path.
file_names is a list of the files contained at that path.

#### walk_path(path='')

Find available files and folders by walking the folder tree. If path
is given, start at the named path. Otherwise start at the top.

This behaves similarly to os.path.walk(path).

For each folder in the cloud account rooted at the given path (and
including that path), yield a 3-tuple:

```default
folder_path, folder_names, file_names
```

folder_path is a string, the full path to the folder. Each folder
is separated by ‘/’. If the folder name includes ‘/’ it becomes ‘%2F’.
folder_names is a list of the folders contained at that path.
file_names is a list of the files contained at that path.

The caller can modify the folder_names in-place to remove entries. This
will prevent those folders from being opened. For example, to show
everything except the contents of the top-level Note folder:

```default
for folder_path, folder_names, file_names in client.walk():
    for folder_name in folder_names:
        print(os.path.join(folder_path, folder_name) + '/')
    for file_name in file_names:
        print(os.path.join(folder_path, file_name))
    if folder_path == "" and 'Note' in folder_names:
        folder_names.remove('Note')
```
