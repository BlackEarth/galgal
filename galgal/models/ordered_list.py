
from . import Model

class OrderedList(Model):
    """A mixin that enables a model class to function as an ordered list. Requires two attributes in the model table:
    * a position attribute (default pos), giving each ordered list entry an integer position in the list
    * zero or more scope attributes (default none), within which the list is ordered. None means the whole table is one list.
    """
    pos_attr = 'pos'    # integer position attribute
    list_scope = []     # scope attributes    
    list_start = 1      # starting number

    def in_list(self):
        """return boolean: does this item have a position?"""
        return self[self.pos_attr] is not None
    
    def pos_at(self, pos=None, cursor=None):
        """insert at given position, or at bottom.
        In a transaction:
        * remove from list
        * set position
        * move lower items down one
        """
        c = cursor or self.db.cursor()
        self.pos_remove(cursor=c)
        self[self.pos_attr] = pos or self.list_start
        self.update(cursor=c)
        self.pos_lower_items_dn(cursor=c)
        if cursor is None:
            c.connection.commit()        
        
    def pos_at_top(self, cursor=None):
        """insert this item at the top of the list"""
        self.pos_at(pos=self.list_start, cursor=cursor)
        
    def pos_at_bottom(self, cursor=None):
        """insert this item at the bottom of the list"""
        c = cursor or self.db.cursor()
        self.pos_remove(cursor=c)
        self[self.pos_attr] = self.bottom_pos(cursor=c) + 1
        self.update(cursor=c)
        if cursor is None: c.connection.commit()

    def pos_up(self, cursor=None):
        """move the item one position higher in the list.
        In a transaction:
        * move the next higher item down one
        * move this item up one
        """
        if not self.in_list(): return
        # if not at top of list:
        # transaction:
        # move the next higher item down one.
        # move this item up one.
        c = cursor or self.db.cursor()
        next = self.item_next_pos_up(cursor=c)
        if next is not None:
            next[self.pos_attr] += 1
            next.update(cursor=c)
            self[self.pos_attr] -= 1
            self.update(cursor=c)
        if cursor is None: c.connection.commit()
        
    def pos_dn(self, cursor=None):
        """move the item one position lower in the list.
        In a transaction:
        * move the next lower item up one.
        * move this item down one.
        """
        if not self.in_list(): return
        c = cursor or self.db.cursor()
        next = self.item_next_pos_dn(cursor=c)
        if next is not None:
            next[self.pos_attr] -= 1
            next.update(cursor=c)
            self[self.pos_attr] += 1
            self.update(cursor=c)
        if cursor is None: c.connection.commit()
        
    def pos_remove(self, cursor=None):
        """remove from the list.
        In a transaction:
        * move lower items up one.
        * set position to null.
        """
        if not self.in_list(): return
        c = cursor or self.db.cursor()
        self.pos_lower_items_up(cursor=c)
        self[self.pos_attr] = None
        self.update(cursor=c)
        if cursor is None: c.connection.commit()

    def pos_lower_items_up(self, cursor=None):
        """move lower items up one position"""
        if not self.in_list(): return
        c = cursor or self.db.cursor()
        # pos >= this item's pos
        wherel = ["%s >= %s" % (self.pos_attr, self[self.pos_attr])]
        # not this item => not the same pk fields
        wherel += [
            "not (%s)" % " and ".join([
                "%s=%s" % (k, self.quote(self[k]))
                for k in self.pk_fields
            ])
        ]
        # in the same pos_scope as this item
        wherel += [
            "%s=%s" % (k, self.quote(self[k]))
            for k in self.list_scope
        ]
        sql = "update %s set %s = %s - 1 where %s" % (
            self.relation, self.pos_attr, self.pos_attr,
            " and ".join(wherel)
        )
        self.db.execute(sql, cursor=c)
        if cursor is None: c.connection.commit()
 
    def pos_lower_items_dn(self, cursor=None):
        """move lower items down one position"""
        if not self.in_list(): return
        c = cursor or self.db.cursor()
        # pos >= this item's position
        wherel = ["%s >= %s" % (self.pos_attr, self[self.pos_attr])]
        # not this item => not the same pk fields
        wherel += [
            "not (%s)" % " and ".join([
                "%s=%s" % (k, self.quote(self[k]))
                for k in self.pk_fields
            ])
        ]
        # in the same pos_scope as this item
        wherel += [
            "%s=%s" % (k, self.quote(self[k]))
            for k in self.list_scope
        ]
        sql = "update %s set %s = %s + 1 where %s" % (
            self.relation, self.pos_attr, self.pos_attr,
            " and ".join(wherel)
        )
        self.db.execute(sql, cursor=c)
        if cursor is None: c.connection.commit()
        
    def item_next_pos_up(self, cursor=None):
        """return the next higher record"""
        c = cursor or self.db.cursor()
        rec = self.select_one(cursor=c, pos=self.pos-1, **self.pos_scope(cursor=c))
        if cursor is None: c.connection.commit()
        return rec
    
    def item_next_pos_dn(self, cursor=None):
        """return the next lower record"""
        c = cursor or self.db.cursor()
        rec = self.select_one(cursor=c, pos=self.pos+1, **self.pos_scope(cursor=c))
        if cursor is None: c.connection.commit()
        return rec

    def bottom_pos(self, cursor=None):
        """return the bottom pos in the list"""
        # get the bottom position after the move
        c = cursor or self.db.cursor()
        r = self.select_one(orderby=self.pos_attr+' desc', cursor=c, where="%s is not null" % self.pos_attr, **self.pos_scope(cursor=c))
        if r is not None:
            pos = r.pos
        else:
            pos = self.list_start - 1        
        if cursor is None: c.connection.commit()
        return pos

    def pos_scope(self, cursor=None):
        """returns a dictionary with the pos_scope of this instance"""
        return {k: self[k] for k in self.list_scope}


def tests():
    """tests of the OrderedList class.
    >>> import amplitude; from amplitude.models import Model
    >>> db=amplitude.testdb()
    >>> db.execute("create table items (id serial primary key, account varchar, pos int)")
    >>> class Item(Model):
    ...     relation = 'items' 
    ...     pk_fields = ['id']
    >>> class OrderedItem(Item, OrderedList):
    ...     list_scope = ['account']         # typical pos_scope: separate list for each account person
    >>> item1 = OrderedItem(db, account='mine'); item1.insert(); item1.pos_at_bottom()
    >>> item2 = OrderedItem(db, account='mine'); item2.insert(); item2.pos_at_bottom()
    >>> item3 = OrderedItem(db, account='mine'); item3.insert(); item3.pos_at_bottom()
    >>> item4 = OrderedItem(db, account='mine'); item4.insert(); item4.pos_at_bottom()
    >>> item5 = OrderedItem(db, account='yours'); item5.insert(); item5.pos_at_bottom()
    >>> item6 = OrderedItem(db, account='yours'); item6.insert(); item6.pos_at_bottom()
    >>> item7 = OrderedItem(db, account='yours'); item7.insert(); item7.pos_at_bottom()
    >>> items = [item1, item2, item3, item4, item5, item6, item7]
    >>> item1.pos, item2.pos, item3.pos, item4.pos, item5.pos, item6.pos, item7.pos
    (1, 2, 3, 4, 1, 2, 3)
    >>> item1.pos_dn()
    >>> for item in items: item.reload()
    >>> item1.pos, item2.pos, item3.pos, item4.pos, item5.pos, item6.pos, item7.pos
    (2, 1, 3, 4, 1, 2, 3)
    >>> item1.pos_dn()
    >>> for item in items: item.reload()
    >>> item1.pos, item2.pos, item3.pos, item4.pos, item5.pos, item6.pos, item7.pos
    (3, 1, 2, 4, 1, 2, 3)
    >>> item1.pos_dn()
    >>> for item in items: item.reload()
    >>> item1.pos, item2.pos, item3.pos, item4.pos, item5.pos, item6.pos, item7.pos
    (4, 1, 2, 3, 1, 2, 3)
    >>> item1.pos_dn()
    >>> for item in items: item.reload()
    >>> item1.pos, item2.pos, item3.pos, item4.pos, item5.pos, item6.pos, item7.pos     # no change - bottom of scope
    (4, 1, 2, 3, 1, 2, 3)
    >>> item2.pos_up()
    >>> for item in items: item.reload()
    >>> item1.pos, item2.pos, item3.pos, item4.pos, item5.pos, item6.pos, item7.pos     # no change - top of scope
    (4, 1, 2, 3, 1, 2, 3)
    >>> item1.pos_at(1)
    >>> for item in items: item.reload()
    >>> item1.pos, item2.pos, item3.pos, item4.pos, item5.pos, item6.pos, item7.pos
    (1, 2, 3, 4, 1, 2, 3)
    >>> item4.pos_at(2)
    >>> for item in items: item.reload()
    >>> item1.pos, item2.pos, item3.pos, item4.pos, item5.pos, item6.pos, item7.pos
    (1, 3, 4, 2, 1, 2, 3)
    >>> item1.pos_remove()
    >>> for item in items: item.reload()
    >>> item1.pos, item2.pos, item3.pos, item4.pos, item5.pos, item6.pos, item7.pos
    (None, 2, 3, 1, 1, 2, 3)
    >>> item1.pos_at_top()
    >>> for item in items: item.reload()
    >>> item1.pos, item2.pos, item3.pos, item4.pos, item5.pos, item6.pos, item7.pos
    (1, 3, 4, 2, 1, 2, 3)
    >>> item4.pos_at_bottom()
    >>> for item in items: item.reload()
    >>> item1.pos, item2.pos, item3.pos, item4.pos, item5.pos, item6.pos, item7.pos
    (1, 2, 3, 4, 1, 2, 3)
    >>> db.execute("drop table items")
    """
        
if __name__ == "__main__":
    import doctest
    doctest.testmod()
