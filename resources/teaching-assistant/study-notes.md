# Study Notes: Introduction to Python

## Topic 1: Variables and Data Types

Python is a dynamically typed language, meaning you don't need to declare variable types explicitly.

**Basic types:**
- `int` — whole numbers, e.g. `x = 42`
- `float` — decimal numbers, e.g. `y = 3.14`
- `str` — text, e.g. `name = "Alice"`
- `bool` — `True` or `False`
- `None` — represents the absence of a value

**Type conversion:**
```python
int("42")     # → 42
str(3.14)     # → "3.14"
float("1.5")  # → 1.5
bool(0)       # → False
bool(1)       # → True
```

Variables are assigned with `=`. Variable names are case-sensitive and cannot start with a digit.

---

## Topic 2: Control Flow

### if / elif / else
```python
x = 10
if x > 10:
    print("greater")
elif x == 10:
    print("equal")
else:
    print("less")
```

Indentation (4 spaces or 1 tab) defines code blocks — there are no braces.

### for loops
Iterate over any iterable:
```python
for i in range(5):     # 0, 1, 2, 3, 4
    print(i)

for char in "hello":   # iterates characters
    print(char)
```

### while loops
```python
count = 0
while count < 3:
    count += 1
```

`break` exits the loop early; `continue` skips to the next iteration.

---

## Topic 3: Functions

Functions are defined with `def`:
```python
def greet(name, greeting="Hello"):
    return f"{greeting}, {name}!"

greet("Alice")            # "Hello, Alice!"
greet("Bob", "Hi")        # "Hi, Bob!"
```

**Key concepts:**
- Parameters can have default values
- `return` exits the function and returns a value; without it, `None` is returned
- Arguments can be passed by position or by keyword
- `*args` collects extra positional arguments as a tuple
- `**kwargs` collects extra keyword arguments as a dict

**Scope:** Variables defined inside a function are local. Use the `global` keyword to modify a module-level variable from within a function (avoid when possible).

---

## Topic 4: Lists and Dictionaries

### Lists
Ordered, mutable sequences:
```python
fruits = ["apple", "banana", "cherry"]
fruits.append("date")         # add to end
fruits.insert(1, "avocado")   # insert at index
fruits.pop()                  # remove last
len(fruits)                   # length
fruits[0]                     # indexing
fruits[1:3]                   # slicing → ["avocado", "banana"]
```

List comprehension: `[x**2 for x in range(5)]` → `[0, 1, 4, 9, 16]`

### Dictionaries
Key-value pairs, unordered (insertion-ordered since Python 3.7):
```python
person = {"name": "Alice", "age": 30}
person["name"]           # "Alice"
person["city"] = "NYC"   # add key
person.get("missing", 0) # safe access with default
person.keys()            # dict_keys(["name", "age", "city"])
person.values()          # dict_values(["Alice", 30, "NYC"])
person.items()           # iterate as (key, value) pairs
```

Keys must be immutable (strings, numbers, tuples). Values can be anything.
