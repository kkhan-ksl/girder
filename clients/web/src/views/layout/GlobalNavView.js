import $ from 'jquery';
import Backbone from 'backbone';

import router from 'girder/router';
import View from 'girder/views/View';
import events from 'girder/events';
import { getCurrentUser } from 'girder/auth';

import LayoutGlobalNavTemplate from 'girder/templates/layout/layoutGlobalNav.pug';

import 'girder/stylesheets/layout/globalNav.styl';


/**
 * This view shows a list of global navigation links that should be
 * displayed at all times.
 */
var LayoutGlobalNavView = View.extend({
    events: {
        'click .g-nav-link': function (event) {
            event.preventDefault(); // so we can keep the href

            var link = $(event.currentTarget);

            router.navigate(link.attr('g-target'), {trigger: true});
            this.deactivateAll();

            // Must call this after calling navigateTo, since that
            // deactivates all global nav links.
            link.parent().addClass('g-active');
            if (this.bannerColor !== '#ffffff') {
                link.css('color', this.bannerColor);
            }
        }
    },

    initialize: function (settings) {
        events.on('g:highlightItem', this.selectForView, this);
        events.on('g:login', this.render, this);
        events.on('g:logout', this.render, this);
        events.on('g:login-changed', this.render, this);

        settings = settings || {};
        if (settings.navItems) {
            this.navItems = settings.navItems;
        } else {
            this.defaultNavItems = [{
                name: 'Collections',
                icon: 'icon-sitemap',
                target: 'collections'
            }, {
                name: 'Users',
                icon: 'icon-user',
                target: 'users'
            }, {
                name: 'Groups',
                icon: 'icon-users',
                target: 'groups'
            }];
        }
        this.parentView = settings.parentView;
        if (this.parentView.cid !== 'view1') {
            this.bannerColor = this.parentView.bannerColor;
            this.textColor = this.parentView._getTextColor(this.bannerColor);
        } else {
            this.textColor = null;
        }

    },

    render: function () {
        var navItems;
        if (this.navItems) {
            navItems = this.navItems;
        } else {
            navItems = this.defaultNavItems;
            if (getCurrentUser() && getCurrentUser().get('admin')) {
                // copy navItems so that this.defaultNavItems is unchanged
                navItems = navItems.slice();
                navItems.push({
                    name: 'Admin console',
                    icon: 'icon-wrench',
                    target: 'admin'
                });
            }
            // Provide an Home link when the brand name is not display, need to be render for being display
            if (this.parentView.$('#g-app-header-container .g-app-title').css('display') === 'none') {
                navItems.unshift({
                    name: 'Home',
                    icon: 'icon-home',
                    target: ''
                });
            }
        }
        this.$el.html(LayoutGlobalNavTemplate({
            navItems: navItems,
            textColor: this.textColor
        }));

        if (Backbone.history.fragment) {
            const target = this.$('[g-target="' + Backbone.history.fragment + '"]');
            target.parent().addClass('g-active');
            target.css('color', this.bannerColor);
        }

        return this;
    },

    /**
     * Highlight the item with the given target attribute, which is the name
     * of the view it navigates to.
     */
    selectForView: function (viewName) {
        this.deactivateAll();
        this.$('[g-name="' + viewName.slice(0, -4) + '"]').parent().addClass('g-active');
        if (this.bannerColor !== '#ffffff') {
                this.$('.g-active').children().css('color', this.bannerColor);
        }
    },

    deactivateAll: function () {
        var options = this.$('.g-global-nav-li')
        options.removeClass('g-active');
        options.children().css('color', this.textColor);
    }
});

export default LayoutGlobalNavView;
