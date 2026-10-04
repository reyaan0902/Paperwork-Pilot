export default function Logo({ light = false }) {
  return (
    <span className={`logo${light ? ' logo--light' : ''}`}>
      <svg viewBox="0 0 32 32" width="28" height="28" aria-hidden="true">
        <rect width="32" height="32" rx="8" className="logo__tile" />
        <path d="M9 17.5l4.5 4.5L23 11" fill="none" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round" className="logo__check" />
      </svg>
      <span>Paperwork Pilot</span>
    </span>
  );
}
