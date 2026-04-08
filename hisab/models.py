from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import String, Boolean, DateTime, Integer, ForeignKey, Float, UniqueConstraint, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

def _now() -> datetime:
    return datetime.now(timezone.utc)

class Base(DeclarativeBase):
    pass

class Owner(Base):

    __tablename__ = "owners"

    villa_id: Mapped[str] = mapped_column(String, primary_key=True)
    owner_name: Mapped[str] = mapped_column(String, nullable=False)
    email: Mapped[str] = mapped_column(String, default="")
    phone: Mapped[str] = mapped_column(String, default="")
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now, onupdate=_now)

    identifiers: Mapped[list["OwnerIdentifier"]] = relationship(back_populates="owner", cascade="all, delete-orphan")

    transactions: Mapped[list["Transaction"]] = relationship(back_populates="owner")
    reconciliations: Mapped[list["Reconciliation"]] = relationship(back_populates="owner")

    def __repr__(self) -> str:
        return f"<Owner villa_id={self.villa_id} name={self.owner_name}>"

class OwnerIdentifier(Base):

    __tablename__ = "owner_identifiers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    
    villa_id: Mapped[str] = mapped_column(ForeignKey("owners.villa_id"), nullable=False)

    identifier_type: Mapped[str] = mapped_column(String, nullable=False)
    identifier_value: Mapped[str] = mapped_column(String, nullable=False)
    confidence: Mapped[str] = mapped_column(String, default="HIGH")
    requires_confirm: Mapped[bool] = mapped_column(Boolean, default=False)
    auto_learned: Mapped[bool] = mapped_column(Boolean, default=False)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)

    owner: Mapped["Owner"] = relationship(back_populates="identifiers")
    
    def __repr__(self) -> str:
        return f"<OwnerIdentifier {self.identifier_type}={self.identifier_value}>"

class Rate(Base):

    __tablename__ = "rates"

    month: Mapped[str] = mapped_column(String, primary_key=True)
    maintenance: Mapped[float] = mapped_column(Float, default=0.0)
    water: Mapped[float] = mapped_column(Float, default=0.0)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now, onupdate=_now)

    @property
    def total_dues(self) -> float:
        return self.maintenance + self.water

    def __repr__(self) -> str:
        return f"<Rate month={self.month} total={self.total_dues}>"

class Transaction(Base):

    __tablename__ = "transactions"
    __table_args__ = (
        UniqueConstraint("value_date", "particulars", "credit", "debit"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    
    transaction_date: Mapped[str] = mapped_column(String, nullable=False)
    value_date: Mapped[str] = mapped_column(String, nullable=False)
    particulars: Mapped[str] = mapped_column(Text, nullable=False)
    cheque_no: Mapped[Optional[str]] = mapped_column(String)
    debit: Mapped[float] = mapped_column(Float, default=0.0)
    credit: Mapped[float] = mapped_column(Float, default=0.0)
    balance: Mapped[float] = mapped_column(Float, default=0.0)

    month: Mapped[str] = mapped_column(String, nullable=False)
    payment_type: Mapped[str] = mapped_column(String, default="OTHER")
    extracted_id: Mapped[str] = mapped_column(String, default="")

    transaction_type: Mapped[str] = mapped_column(String, default="UNMATCHED")
    villa_id: Mapped[Optional[str]] = mapped_column(ForeignKey("owners.villa_id"))
    manually_tagged: Mapped[bool] = mapped_column(Boolean, default=False)
    notes: Mapped[str] = mapped_column(Text, default="")

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)

    owner: Mapped[Optional["Owner"]] = relationship(back_populates="transactions")

    def __repr__(self) -> str:
        return f"<Transaction {self.value_date} {self.transaction_type} {self.credit or self.debit}>"

class Reconciliation(Base):

    __tablename__ = "reconciliation"
    __table_args__ = (UniqueConstraint("month", "villa_id"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    month: Mapped[str] = mapped_column(String, nullable=False)
    villa_id: Mapped[str] = mapped_column(ForeignKey("owners.villa_id"), nullable=False)
    dues: Mapped[float] = mapped_column(Float, default=0.0)
    paid: Mapped[float] = mapped_column(Float, default=0.0)
    carry_forward: Mapped[float] = mapped_column(Float, default=0.0)
    last_payment_date: Mapped[Optional[str]] = mapped_column(String)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now, onupdate=_now)

    owner: Mapped["Owner"] = relationship(back_populates="reconciliations")


    @property
    def outstanding(self) -> float:
        return max(0.0, self.dues - self.paid - self.carry_forward)

    @property
    def status(self) -> str:
        total_paid = self.paid + self.carry_forward
        if total_paid >= self.dues:
            return "PAID" if total_paid == self.dues else "ADVANCE"
        elif total_paid > 0:
            return "PARTIAL"
        return "UNPAID"

    def __repr__(self) -> str:
        return f"<Reconciliation month={self.month} villa={self.villa_id} status={self.status}>"

class SocietySummary(Base):

    __tablename__ = "society_summary"

    month: Mapped[str] = mapped_column(String, primary_key=True)
    total_dues_raised: Mapped[float] = mapped_column(Float, default=0.0)
    total_collected: Mapped[float] = mapped_column(Float, default=0.0)
    total_outstanding: Mapped[float] = mapped_column(Float, default=0.0)
    total_interest: Mapped[float] = mapped_column(Float, default=0.0)
    total_expenses: Mapped[float] = mapped_column(Float, default=0.0)
    closing_bank_balance: Mapped[float] = mapped_column(Float, default=0.0)
    carry_forward_in: Mapped[float] = mapped_column(Float, default=0.0)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now, onupdate=_now)

    def __repr__(self) -> str:
        return f"<SocietySummary month={self.month} collected={self.total_collected}>"

class ProcessedFile(Base):

    __tablename__ = "processed_files"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    filename: Mapped[str] = mapped_column(String, nullable=False)
    file_hash: Mapped[str] = mapped_column(String, nullable=False, unique=True)

    row_count: Mapped[int] = mapped_column(Integer, default=0)
    imported_count: Mapped[int] = mapped_column(Integer, default=0)
    skipped_count: Mapped[int] = mapped_column(Integer, default=0)

    status: Mapped[str] = mapped_column(String, default="PROCESSED")
    failed_reason: Mapped[Optional[str]] = mapped_column(Text)

    processed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)

    def __repr__(self) -> str:
        return f"<ProcessedFile {self.filename} status={self.status}>"
