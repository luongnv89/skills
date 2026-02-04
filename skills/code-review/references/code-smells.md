# Code Smells Catalog

## Table of Contents

1. [Bloaters](#bloaters)
2. [Object-Orientation Abusers](#object-orientation-abusers)
3. [Change Preventers](#change-preventers)
4. [Dispensables](#dispensables)
5. [Couplers](#couplers)

---

## Bloaters

Code that has grown so large it becomes hard to work with.

### Long Method

**Signs**: Method >20 lines, multiple levels of abstraction, hard to name.

**Fix**: Extract Method - break into smaller, well-named methods.

```javascript
// Bad
function processOrder(order) {
  // validate (10 lines)
  // calculate totals (15 lines)
  // apply discounts (10 lines)
  // save to database (5 lines)
  // send notification (10 lines)
}

// Good
function processOrder(order) {
  validateOrder(order);
  const totals = calculateTotals(order);
  const finalPrice = applyDiscounts(totals);
  saveOrder(order, finalPrice);
  notifyCustomer(order);
}
```

### Large Class

**Signs**: Class >200 lines, multiple responsibilities, too many instance variables.

**Fix**: Extract Class, Extract Subclass, or Extract Interface.

### Long Parameter List

**Signs**: Method with >3 parameters.

**Fix**: Introduce Parameter Object, Preserve Whole Object, or use Builder pattern.

```python
# Bad
def create_user(name, email, age, address, city, country, phone, role):
    pass

# Good
def create_user(user_data: UserData):
    pass

# Or use builder
User.builder().name("John").email("john@example.com").build()
```

### Primitive Obsession

**Signs**: Using primitives instead of small objects (money, phone, email).

**Fix**: Replace with Value Object.

```typescript
// Bad
function sendMoney(amount: number, currency: string) {}

// Good
class Money {
  constructor(public amount: number, public currency: Currency) {}
}
function sendMoney(money: Money) {}
```

### Data Clumps

**Signs**: Same group of variables appear together repeatedly.

**Fix**: Extract Class for the clump.

```java
// Bad - these three always appear together
void setCoordinates(int x, int y, int z) {}
void calculateDistance(int x1, int y1, int z1, int x2, int y2, int z2) {}

// Good
class Point3D { int x, y, z; }
void setCoordinates(Point3D point) {}
void calculateDistance(Point3D from, Point3D to) {}
```

---

## Object-Orientation Abusers

Incorrect application of OO principles.

### Switch Statements

**Signs**: Same switch on type appears in multiple places.

**Fix**: Replace with polymorphism.

```python
# Bad
def calculate_area(shape):
    if shape.type == "circle":
        return 3.14 * shape.radius ** 2
    elif shape.type == "rectangle":
        return shape.width * shape.height

# Good
class Circle:
    def area(self):
        return 3.14 * self.radius ** 2

class Rectangle:
    def area(self):
        return self.width * self.height
```

### Temporary Field

**Signs**: Instance variable only used in certain circumstances.

**Fix**: Extract Class or use Null Object.

### Refused Bequest

**Signs**: Subclass doesn't use inherited methods/properties.

**Fix**: Replace Inheritance with Delegation, or Extract Superclass.

### Alternative Classes with Different Interfaces

**Signs**: Two classes do similar things but have different method names.

**Fix**: Rename Methods, Extract Superclass, or unify interfaces.

---

## Change Preventers

Code that makes changes difficult.

### Divergent Change

**Signs**: One class is changed for multiple different reasons.

**Violation**: Single Responsibility Principle.

**Fix**: Extract Class - one class per reason to change.

```javascript
// Bad - User class changes for auth, profile, and billing reasons
class User {
  authenticate() {}
  updateProfile() {}
  processBilling() {}
}

// Good
class AuthService {}
class UserProfile {}
class BillingService {}
```

### Shotgun Surgery

**Signs**: One change requires edits to many classes.

**Fix**: Move Method/Field to consolidate related code.

### Parallel Inheritance Hierarchies

**Signs**: Creating a subclass in one hierarchy requires creating one in another.

**Fix**: Merge hierarchies or use composition.

---

## Dispensables

Code that adds no value.

### Comments (Excessive)

**Signs**: Comments explain what code does, not why.

**Fix**: Extract Method with descriptive name, rename variables.

```python
# Bad
# Check if user is adult
if user.age >= 18:

# Good
if user.is_adult():
```

### Duplicate Code

**Signs**: Same code structure in multiple places.

**Fix**: Extract Method, Extract Class, Pull Up Method, or Form Template Method.

### Lazy Class

**Signs**: Class that doesn't do enough to justify its existence.

**Fix**: Inline Class or Collapse Hierarchy.

### Data Class

**Signs**: Class with only fields and getters/setters, no behavior.

**Fix**: Move behavior into the class.

### Dead Code

**Signs**: Unreachable code, unused variables, unused parameters.

**Fix**: Delete it. Version control has history.

### Speculative Generality

**Signs**: "We might need this someday" code.

**Fix**: Delete unused abstractions. YAGNI (You Aren't Gonna Need It).

---

## Couplers

Code with excessive coupling between classes.

### Feature Envy

**Signs**: Method uses more features from another class than its own.

**Fix**: Move Method to the class it envies.

```ruby
# Bad - Order envies Customer
class Order
  def discount_price
    if customer.loyalty_years > 5 && customer.total_purchases > 10000
      price * 0.9
    else
      price
    end
  end
end

# Good - Move to Customer
class Customer
  def discount_for(price)
    eligible_for_discount? ? price * 0.9 : price
  end
end
```

### Inappropriate Intimacy

**Signs**: Classes access each other's private parts excessively.

**Fix**: Move Method/Field, Extract Class, or Hide Delegate.

### Message Chains

**Signs**: `a.getB().getC().getD().doSomething()`

**Fix**: Hide Delegate - add wrapper method.

```java
// Bad
order.getCustomer().getAddress().getCity().getName();

// Good
order.getDeliveryCity();
```

### Middle Man

**Signs**: Class that only delegates to another class.

**Fix**: Remove Middle Man or Inline Class.

### Incomplete Library Class

**Signs**: Library class missing needed functionality.

**Fix**: Introduce Foreign Method or Extension.

---

## Quick Detection Patterns

| Smell | Quick Check |
|-------|-------------|
| Long Method | >20 lines or >2 indentation levels |
| Large Class | >200 lines or >10 methods |
| Long Parameter List | >3 parameters |
| Duplicate Code | Grep for similar patterns |
| Dead Code | Unused imports, unreachable branches |
| Feature Envy | Method references other object >3 times |
| Message Chains | >2 dots in chain |
| God Class | Class name ends in "Manager", "Handler", "Processor" |
