import * as DropdownMenu from "@radix-ui/react-dropdown-menu";

// Toolbar above the invoices table. The Filter menu uses the app's existing
// Radix dropdown; every menu in this app is built the same way.
export function Toolbar({ onFilter }) {
  return (
    <div className="toolbar">
      <DropdownMenu.Root>
        <DropdownMenu.Trigger className="toolbar-button">Filter</DropdownMenu.Trigger>
        <DropdownMenu.Portal>
          <DropdownMenu.Content className="menu" sideOffset={4}>
            <DropdownMenu.Item className="menu-item" onSelect={() => onFilter("paid")}>Paid</DropdownMenu.Item>
            <DropdownMenu.Item className="menu-item" onSelect={() => onFilter("overdue")}>Overdue</DropdownMenu.Item>
            <DropdownMenu.Item className="menu-item" onSelect={() => onFilter("draft")}>Draft</DropdownMenu.Item>
          </DropdownMenu.Content>
        </DropdownMenu.Portal>
      </DropdownMenu.Root>
    </div>
  );
}
