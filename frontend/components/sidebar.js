// components/sidebar.js

const sidebarHTML = `
<aside class="sidebar-drawer fixed left-0 top-14 h-[calc(100%-3.5rem)] w-[280px] bg-white dark:bg-slate-900 border-r border-pink-100 dark:border-pink-900/20 z-50 overflow-y-auto">
    <div class="flex flex-col h-full">
        <div class="p-6 border-b border-pink-50 dark:border-pink-900/10">
            <div class="flex flex-col">
                <span class="font-display font-bold text-lg tracking-tight text-slate-900 dark:text-white">SWIFTY</span>
            </div>
        </div>
        
        <nav class="flex-1 px-4 py-4 space-y-1" id="sidebar-nav">
            <a href="Coordinator_homepage.html" class="nav-link flex items-center gap-3 px-4 py-3 text-slate-600 dark:text-slate-400 hover:bg-pink-50 dark:hover:bg-pink-900/10 rounded-xl transition-colors mb-2">
                <span class="material-icons-round text-xl">dashboard</span>
                <span class="text-sm">Dashboard</span>
            </a>
            <a href="Finances.html" class="nav-link flex items-center gap-3 px-4 py-3 text-slate-600 dark:text-slate-400 hover:bg-pink-50 dark:hover:bg-pink-900/10 rounded-xl transition-colors mt-2">
                <span class="material-icons-round text-xl">account_balance_wallet</span>
                <span class="text-sm">Finances</span>
            </a>
            <a href="permissionletter.html" class="nav-link flex items-center gap-3 px-4 py-3 text-slate-600 dark:text-slate-400 hover:bg-pink-50 dark:hover:bg-pink-900/10 rounded-xl transition-colors mt-2">
                <span class="material-icons-round text-xl">description</span>
                <span class="text-sm">Permission Letter</span>
            </a>
            <a href="Mou.html" class="nav-link flex items-center gap-3 px-4 py-3 text-slate-600 dark:text-slate-400 hover:bg-pink-50 dark:hover:bg-pink-900/10 rounded-xl transition-colors mt-2">
                <span class="material-icons-round text-xl">assignment</span>
                <span class="text-sm">MOU Form</span>
            </a>
            <a href="Venue_booking.html" class="nav-link flex items-center gap-3 px-4 py-3 text-slate-600 dark:text-slate-400 hover:bg-pink-50 dark:hover:bg-pink-900/10 rounded-xl transition-colors mt-2">
                <span class="material-icons-round text-xl">event_seat</span>
                <span class="text-sm">Venue Booking</span>
            </a>
            <a href="past requests.html" class="nav-link flex items-center gap-3 px-4 py-3 text-slate-600 dark:text-slate-400 hover:bg-pink-50 dark:hover:bg-pink-900/10 rounded-xl transition-colors mt-2">
                <span class="material-icons-round text-xl">history</span>
                <span class="text-sm">Past Requests</span>
            </a>
        </nav>
        <div class="p-4 border-t border-pink-50 dark:border-pink-900/10"></div>
    </div>
</aside>
`;

// 1. Inject the HTML into the container
document.getElementById('sidebar-container').innerHTML = sidebarHTML;

// 2. Automatically highlight the active page based on the URL
const currentPath = window.location.pathname.split('/').pop().toLowerCase();
const navLinks = document.querySelectorAll('#sidebar-nav .nav-link');

navLinks.forEach(link => {
    // If the link's href matches the current URL, make it active
    const linkPath = link.getAttribute('href').toLowerCase();
    if (linkPath === currentPath || (currentPath === '' && linkPath === 'coordinator_homepage.html')) {
        link.classList.remove('text-slate-600', 'dark:text-slate-400', 'hover:bg-pink-50', 'dark:hover:bg-pink-900/10');
        link.classList.add('nav-item-active', 'text-slate-900', 'dark:text-white');
    }
});