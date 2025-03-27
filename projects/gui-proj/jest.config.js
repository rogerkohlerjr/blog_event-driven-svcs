module.exports = {
  preset: 'ts-jest',
  testEnvironment: 'jsdom', // Use 'node' if you're testing non-DOM code
  testMatch: ['**/tests/**/*.test.ts'], // Adjust the pattern to match your test files
  moduleNameMapper: {
    '^@/(.*)$': '<rootDir>/src/$1', // Optional: Map paths if you're using aliases
  },
};
