import React from "react";
import { useLanguage } from "../i18n/LanguageContext";

export default function LanguageSwitcher() {
  const { language, setLanguage } = useLanguage();

  return (
    <select
      className="language-switcher"
      value={language}
      onChange={(e) => setLanguage(e.target.value)}
      aria-label="Language / भाषा"
    >
      <option value="en">English</option>
      <option value="mr">मराठी</option>
    </select>
  );
}
