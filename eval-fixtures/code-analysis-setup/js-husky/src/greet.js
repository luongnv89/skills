export function greet(name) {
  const who = name && name.trim() ? name.trim() : "world";
  return `Hello, ${who}!`;
}
