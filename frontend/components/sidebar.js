// components/sidebar.js

const sidebarHTML = `
<aside class="sidebar-drawer fixed left-0 top-16 h-[calc(100%-4rem)] w-[260px] bg-white dark:bg-slate-900 border-r border-pink-100 dark:border-pink-900/20 z-50 overflow-y-auto shadow-sm">
    <div class="flex flex-col h-full">
        <nav class="flex-1 px-4 py-6 space-y-2" id="sidebar-nav">
            <a href="Coordinator_homepage.html" class="nav-link flex items-center gap-3 px-4 py-3 text-slate-600 dark:text-slate-400 hover:bg-pink-50 dark:hover:bg-pink-900/10 rounded-xl transition-colors">
                <span class="material-icons-round text-xl">dashboard</span>
                <span class="text-sm">Dashboard</span>
            </a>
            <a href="Finances.html" class="nav-link flex items-center gap-3 px-4 py-3 text-slate-600 dark:text-slate-400 hover:bg-pink-50 dark:hover:bg-pink-900/10 rounded-xl transition-colors">
                <span class="material-icons-round text-xl">account_balance_wallet</span>
                <span class="text-sm">Finances</span>
            </a>
            <a href="permissionletter.html" class="nav-link flex items-center gap-3 px-4 py-3 text-slate-600 dark:text-slate-400 hover:bg-pink-50 dark:hover:bg-pink-900/10 rounded-xl transition-colors">
                <span class="material-icons-round text-xl">description</span>
                <span class="text-sm">Permission Letter</span>
            </a>
            <a href="Mou.html" class="nav-link flex items-center gap-3 px-4 py-3 text-slate-600 dark:text-slate-400 hover:bg-pink-50 dark:hover:bg-pink-900/10 rounded-xl transition-colors">
                <span class="material-icons-round text-xl">assignment</span>
                <span class="text-sm">MOU Form</span>
            </a>
            <a href="Venue_booking.html" class="nav-link flex items-center gap-3 px-4 py-3 text-slate-600 dark:text-slate-400 hover:bg-pink-50 dark:hover:bg-pink-900/10 rounded-xl transition-colors">
                <span class="material-icons-round text-xl">event_seat</span>
                <span class="text-sm">Venue Booking</span>
            </a>
            <a href="past requests.html" class="nav-link flex items-center gap-3 px-4 py-3 text-slate-600 dark:text-slate-400 hover:bg-pink-50 dark:hover:bg-pink-900/10 rounded-xl transition-colors">
                <span class="material-icons-round text-xl">history</span>
                <span class="text-sm">Past Requests</span>
            </a>
        </nav>
    </div>
</aside>
`;

document.getElementById('sidebar-container').outerHTML = sidebarHTML;

// Automatically highlight the active page based on the URL
const currentPath = decodeURIComponent(window.location.pathname).toLowerCase();
const navLinks = document.querySelectorAll('#sidebar-nav .nav-link');

navLinks.forEach(link => {
    // 2. Get the href of the link and make it lowercase
    const linkHref = link.getAttribute('href').toLowerCase();

    // 3. Check if the current URL ends with this specific file name
    if (currentPath.endsWith(linkHref) || (currentPath === '/' && linkHref === 'coordinator_homepage.html')) {
        
        link.classList.remove('text-slate-600', 'dark:text-slate-400', 'hover:bg-pink-50', 'dark:hover:bg-pink-900/10');
        
        // Add the GREY active classes
        link.classList.add(
            'bg-slate-100', 'dark:bg-slate-800', 
            'text-slate-900', 'dark:text-white', 
            'font-bold'
        );
    }
});