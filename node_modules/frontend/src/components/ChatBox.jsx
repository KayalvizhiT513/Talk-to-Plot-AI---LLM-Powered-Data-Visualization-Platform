import { useState } from "react";

export default function ChatBox({ onSubmit, disabled }) {
  const [value, setValue] = useState("");

  const handleSubmit = (event) => {
    event.preventDefault();
    if (disabled) {
      return;
    }
    onSubmit(value, () => setValue(""));
  };

  return (
    <form className="chatbox-form" onSubmit={handleSubmit}>
      <input
        value={value}
        onChange={(event) => setValue(event.target.value)}
        placeholder="Enter prompt..."
        disabled={disabled}
      />
      <button type="submit" disabled={disabled}>
        {disabled ? "Sending" : "Send"}
      </button>
    </form>
  );
}
