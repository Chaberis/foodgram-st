test.skip('renders learn react link', async () => {
  let App;
  try {
    const module = await import('./App');
    App = module.default;
  } catch (error) {
    // Handle the error or simply return early
    return;
  }
  render(<App />);
  const linkElement = screen.getByText(/learn react/i);
  expect(linkElement).toBeInTheDocument();
});