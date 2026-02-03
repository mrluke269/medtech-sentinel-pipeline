# Python Fundamentals: From Basics to Our Code

This guide starts with the absolute basics and gradually builds up to understand the refactored code. Each section builds on the previous one.

---

## Level 1: Variables (The Foundation)

### What is a Variable?

A variable is a **container** that holds a value.

```python
# Simple variables
name = "Luke"
age = 30
is_active = True
```

**Think of it like:**
- A box labeled "name" containing "Luke"
- A box labeled "age" containing 30

### Using Variables

```python
name = "Luke"
print(name)  # Prints: Luke

age = 30
next_year = age + 1  # next_year = 31
```

**Key concept:** Variables store values so you can reuse them.

---

## Level 2: Functions and Parameters

### What is a Function?

A function is a **reusable block of code** that does something.

```python
def greet(name):
    return f"Hello, {name}!"

result = greet("Luke")
# result = "Hello, Luke!"
```

### What is a Parameter?

A **parameter** is a variable that a function expects you to provide.

```python
def greet(name):  # 'name' is a parameter
    return f"Hello, {name}!"

greet("Luke")    # "Luke" is the argument (the value you pass)
```

**Breaking it down:**
- `name` is the **parameter** (the placeholder)
- `"Luke"` is the **argument** (the actual value)

### Multiple Parameters

```python
def introduce(name, age):
    return f"I'm {name} and I'm {age} years old"

introduce("Luke", 30)
# Returns: "I'm Luke and I'm 30 years old"
```

**Key concept:** Parameters let functions accept different values each time they're called.

---

## Level 3: Default Parameters

### What is a Default Parameter?

A default parameter has a **pre-set value** that's used if you don't provide one.

```python
def greet(name, greeting="Hello"):
    return f"{greeting}, {name}!"

greet("Luke")           # Uses default: "Hello, Luke!"
greet("Luke", "Hi")     # Overrides: "Hi, Luke!"
```

**What's happening:**
- `greeting="Hello"` means: "If you don't provide greeting, use 'Hello'"
- You can still override it by passing a value

### In Our Code (Simplified)

```python
def build_s3_path(product_code, start_date, end_date, config=CONFIG):
    # If you don't pass config, it uses CONFIG
    pass
```

**Key concept:** Default parameters make functions easier to use - you only need to provide what's different.

---

## Level 4: Types and Type Hints

### What is a Type?

A **type** tells you what kind of data something is.

```python
name = "Luke"      # Type: str (string)
age = 30           # Type: int (integer)
is_active = True   # Type: bool (boolean)
```

### Type Hints (Optional Documentation)

Type hints tell you what type a variable or parameter should be:

```python
def greet(name: str) -> str:
    # name: str means "name should be a string"
    # -> str means "this function returns a string"
    return f"Hello, {name}!"
```

**Important:** Type hints are **optional** in Python. This works too:
```python
def greet(name):
    return f"Hello, {name}!"
```

**Key concept:** Type hints are documentation - they help you understand code but don't change how it works.

---

## Level 5: Lists and Dictionaries

### Lists (Collections of Items)

```python
# A list of strings
names = ["Luke", "Sarah", "John"]

# Access items by position (index)
first_name = names[0]  # "Luke"
second_name = names[1]  # "Sarah"

# Add items
names.append("Mike")  # names = ["Luke", "Sarah", "John", "Mike"]
```

### Dictionaries (Key-Value Pairs)

```python
# A dictionary stores pairs: key → value
person = {
    "name": "Luke",
    "age": 30,
    "city": "Seattle"
}

# Access values using keys
name = person["name"]    # "Luke"
age = person["age"]      # 30

# Add or change values
person["email"] = "luke@example.com"
```

**Key concept:** Dictionaries let you look up values by name (key) instead of position.

---

## Level 6: Classes (Blueprints)

### What is a Class?

A **class** is a **blueprint** for creating objects. Think of it like a cookie cutter.

```python
# Define a class (the blueprint)
class Person:
    def __init__(self, name, age):
        self.name = name
        self.age = age
    
    def introduce(self):
        return f"I'm {self.name} and I'm {self.age}"

# Create instances (actual objects)
person1 = Person("Luke", 30)
person2 = Person("Sarah", 25)

# Use the instances
print(person1.introduce())  # "I'm Luke and I'm 30"
print(person2.introduce())  # "I'm Sarah and I'm 25"
```

**Breaking it down:**
- `class Person:` = "Here's the blueprint"
- `person1 = Person("Luke", 30)` = "Create an actual person using the blueprint"
- `person1` is an **instance** (a real object created from the class)

### Simple Analogy

```
Class = Cookie Cutter (the blueprint)
Instance = Cookie (the actual thing made from the cutter)

CookieCutter → [cut] → Cookie
Person → [create] → person1
```

**Key concept:** A class defines what an object can have and do. An instance is an actual object created from that class.

---

## Level 7: Instances and Attributes

### What is an Instance?

An **instance** is a **real object** created from a class.

```python
class Person:
    def __init__(self, name, age):
        self.name = name    # These are attributes
        self.age = age

# Create instances
person1 = Person("Luke", 30)   # person1 is an instance
person2 = Person("Sarah", 25)  # person2 is another instance

# Access attributes (the data stored in the instance)
print(person1.name)  # "Luke"
print(person1.age)   # 30
print(person2.name)  # "Sarah"
```

### Attributes

**Attributes** are variables that belong to an instance:

```python
person1.name  # "Luke" - this is an attribute
person1.age   # 30 - this is an attribute
```

**Key concept:** Each instance has its own attributes. `person1.name` and `person2.name` are different.

---

## Level 8: Dataclasses (Simplified Classes)

### What is a Dataclass?

A **dataclass** is a **simpler way to create classes** that mainly store data.

### Regular Class (Verbose)

```python
class Person:
    def __init__(self, name, age, city):
        self.name = name
        self.age = age
        self.city = city
```

### Dataclass (Simpler)

```python
from dataclasses import dataclass

@dataclass
class Person:
    name: str
    age: int
    city: str
```

**Both do the same thing!** The dataclass version is just shorter.

### Using a Dataclass

```python
from dataclasses import dataclass

@dataclass
class Person:
    name: str
    age: int
    city: str

# Create an instance
person1 = Person(name="Luke", age=30, city="Seattle")

# Access attributes
print(person1.name)  # "Luke"
print(person1.age)   # 30
print(person1.city)  # "Seattle"
```

**Key concept:** Dataclasses are just a convenient way to create classes that store data. They're still classes, just easier to write.

---

## Level 9: Our PipelineConfig (Step by Step)

Now let's understand the actual code!

### Step 1: The Dataclass Definition

```python
from dataclasses import dataclass

@dataclass
class PipelineConfig:
    FDA_API_BASE_URL: str = 'https://api.fda.gov/device/event.json'
    API_LIMIT: int = 1000
    S3_BUCKET: str = 'medtech-sentinel-raw-luke'
    # ... more settings ...
```

**What this means:**
- `@dataclass` = "Make this a dataclass (simpler class)"
- `class PipelineConfig:` = "This is a blueprint called PipelineConfig"
- `FDA_API_BASE_URL: str = '...'` = "An attribute that's a string with a default value"

**Think of it like:**
```
PipelineConfig = A form with fields:
- FDA_API_BASE_URL: [https://api.fda.gov/device/event.json]
- API_LIMIT: [1000]
- S3_BUCKET: [medtech-sentinel-raw-luke]
```

### Step 2: Creating an Instance

```python
# Global config instance
CONFIG = PipelineConfig()
```

**What this means:**
- `PipelineConfig()` = "Create an instance using the PipelineConfig blueprint"
- `CONFIG = ...` = "Store this instance in a variable called CONFIG"
- `CONFIG` is now a **global variable** (available everywhere in the file)

**What CONFIG contains:**
```python
CONFIG = PipelineConfig()
# CONFIG now has:
# - CONFIG.FDA_API_BASE_URL = 'https://api.fda.gov/device/event.json'
# - CONFIG.API_LIMIT = 1000
# - CONFIG.S3_BUCKET = 'medtech-sentinel-raw-luke'
# - etc.
```

### Step 3: Using CONFIG in a Function

```python
def build_s3_path(
    product_code: str,
    start_date: str,
    end_date: str,
    config: PipelineConfig = CONFIG  # ← This line!
) -> Tuple[str, str]:
    folder = config.PRODUCT_FOLDERS.get(product_code)
    # ...
```

**Breaking it down:**
- `config: PipelineConfig` = "The parameter 'config' should be a PipelineConfig object"
- `= CONFIG` = "If you don't provide config, use the global CONFIG"
- Inside the function, `config` is a PipelineConfig instance

### Step 4: Accessing Attributes

```python
def build_s3_path(..., config: PipelineConfig = CONFIG):
    folder = config.PRODUCT_FOLDERS.get(product_code)
    #           ↑
    #           Access the PRODUCT_FOLDERS attribute of the config object
    
    full_s3_path = f"{config.S3_DATA_PREFIX}/{folder}/{filename}"
    #                  ↑
    #                  Access the S3_DATA_PREFIX attribute
```

**What's happening:**
- `config` is a PipelineConfig instance
- `config.PRODUCT_FOLDERS` accesses the PRODUCT_FOLDERS attribute
- `config.S3_DATA_PREFIX` accesses the S3_DATA_PREFIX attribute

---

## Level 10: Complete Example (Simplified Version)

Let's create a simple version to see it all work together:

```python
from dataclasses import dataclass

# Step 1: Define the class (blueprint)
@dataclass
class AppConfig:
    api_url: str = 'https://api.example.com'
    timeout: int = 30
    retries: int = 3

# Step 2: Create a global instance
DEFAULT_CONFIG = AppConfig()

# Step 3: Use it in a function
def make_request(endpoint, config: AppConfig = DEFAULT_CONFIG):
    # config is an AppConfig instance
    full_url = f"{config.api_url}/{endpoint}"
    # Use config.timeout, config.retries, etc.
    return full_url

# Step 4: Call the function
result = make_request("users")
# Inside the function:
# - config = DEFAULT_CONFIG (the default)
# - config.api_url = 'https://api.example.com'
# - full_url = 'https://api.example.com/users'
```

---

## Level 11: Understanding Our Actual Code

Now let's trace through the real code:

### The PipelineConfig Class

```python
@dataclass
class PipelineConfig:
    FDA_API_BASE_URL: str = 'https://api.fda.gov/device/event.json'
    API_LIMIT: int = 1000
    S3_BUCKET: str = 'medtech-sentinel-raw-luke'
    S3_DATA_PREFIX: str = 'data'
    PRODUCT_FOLDERS: Dict[str, str] = None
    # ... more ...
```

**This is:**
- A class (blueprint) that defines what configuration settings exist
- Each line is an attribute with a default value

### The CONFIG Instance

```python
CONFIG = PipelineConfig()
```

**This creates:**
- An actual object (instance) with all those default values
- Stored in a global variable called `CONFIG`

**CONFIG now contains:**
```python
CONFIG.FDA_API_BASE_URL = 'https://api.fda.gov/device/event.json'
CONFIG.API_LIMIT = 1000
CONFIG.S3_BUCKET = 'medtech-sentinel-raw-luke'
CONFIG.S3_DATA_PREFIX = 'data'
# etc.
```

### Using It in Functions

```python
def extract_fda_events(
    product_code: str,
    start_date: str,
    end_date: str,
    config: PipelineConfig = CONFIG  # ← Default parameter
) -> List[Dict[str, Any]]:
    
    # Use config attributes
    data = fetch_fda_api_page(
        config.FDA_API_BASE_URL,  # ← Access attribute
        search_query,
        skip,
        config.API_LIMIT          # ← Access attribute
    )
```

**What happens when you call it:**

```python
# Call without config (uses default)
events = extract_fda_events('DYE', '20240101', '20240107')
# Inside function: config = CONFIG
# So config.FDA_API_BASE_URL = CONFIG.FDA_API_BASE_URL
```

---

## Level 12: Visual Summary

### The Complete Picture

```
1. Define the Class (Blueprint)
   ┌─────────────────────────────┐
   │ @dataclass                  │
   │ class PipelineConfig:        │
   │   API_URL = "..."            │
   │   BUCKET = "..."             │
   └─────────────────────────────┘
              │
              │ creates
              ▼
2. Create an Instance
   ┌─────────────────────────────┐
   │ CONFIG = PipelineConfig()   │
   │                             │
   │ CONFIG.API_URL = "..."      │
   │ CONFIG.BUCKET = "..."       │
   └─────────────────────────────┘
              │
              │ used as default
              ▼
3. Function Parameter
   ┌─────────────────────────────┐
   │ def my_func(                 │
   │   config: PipelineConfig    │
   │   = CONFIG                   │
   │ ):                           │
   │   config.API_URL             │
   └─────────────────────────────┘
```

---

## Key Concepts Summary

| Concept | What It Is | Example |
|---------|------------|---------|
| **Variable** | Container for a value | `name = "Luke"` |
| **Parameter** | Function input placeholder | `def greet(name):` |
| **Type** | What kind of data | `str`, `int`, `bool` |
| **Class** | Blueprint for objects | `class Person:` |
| **Instance** | Actual object from class | `person1 = Person()` |
| **Attribute** | Data stored in instance | `person1.name` |
| **Dataclass** | Simplified class syntax | `@dataclass class Person:` |
| **Default Parameter** | Pre-set function value | `def func(x=5):` |
| **Global Variable** | Available everywhere | `CONFIG = ...` |

---

## Common Questions

### Q: Is CONFIG a variable or an instance?
**A:** Both! `CONFIG` is a **variable** that stores an **instance**.

```python
CONFIG = PipelineConfig()
# CONFIG = variable name
# PipelineConfig() = creates an instance
# CONFIG stores that instance
```

### Q: What's the difference between a class and an instance?
**A:** 
- **Class** = Cookie cutter (blueprint)
- **Instance** = Cookie (actual thing)

```python
class Person:        # Class (blueprint)
    pass

person1 = Person()   # Instance (actual object)
person2 = Person()   # Another instance
```

### Q: Why use `config: PipelineConfig = CONFIG`?
**A:** 
- Most of the time, use the default `CONFIG`
- Sometimes, you might want a different config (testing, different environment)
- The default makes it easy to use, but you can override it

### Q: What does `config.PRODUCT_FOLDERS` mean?
**A:**
- `config` is a PipelineConfig instance
- `.PRODUCT_FOLDERS` accesses the PRODUCT_FOLDERS attribute
- Like `person.name` accesses the name attribute

---

## Practice Exercise

Try to understand this step by step:

```python
from dataclasses import dataclass

@dataclass
class Settings:
    api_key: str = "default-key"
    timeout: int = 30

DEFAULT_SETTINGS = Settings()

def make_api_call(endpoint, settings: Settings = DEFAULT_SETTINGS):
    url = f"https://api.com/{endpoint}"
    key = settings.api_key
    return f"Calling {url} with key {key}"

result = make_api_call("users")
```

**Questions:**
1. What is `Settings`? (Answer: A class/dataclass)
2. What is `DEFAULT_SETTINGS`? (Answer: An instance of Settings)
3. What is `settings` in the function? (Answer: A parameter)
4. What does `settings.api_key` do? (Answer: Accesses the api_key attribute)

---

## Next Steps

Now that you understand:
- Variables, parameters, types
- Classes and instances
- Dataclasses
- Default parameters
- Global variables

You can read the refactored code and understand:
- `config: PipelineConfig = CONFIG` means "parameter config is a PipelineConfig, defaults to CONFIG"
- `config.S3_BUCKET` accesses the S3_BUCKET attribute of the config instance
- `CONFIG` is a global instance that stores all your settings

The code is just combining these concepts!
