// Plans shown on /pricing and enforced at checkout.
export const PLANS = [
  { id: "free", name: "Free", priceMonthly: 0, invoicesPerMonth: 3 },
  { id: "pro", name: "Pro", priceMonthly: 9, invoicesPerMonth: Infinity, stripePrice: "price_pro_monthly" },
];
